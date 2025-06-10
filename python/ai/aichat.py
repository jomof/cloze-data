import json
from typing import Any, Dict, List

from google import genai
from google.genai import types

import python.gcp
from python.ai.util import parse_and_validate_schema

# Gen AI API is at https://github.com/googleapis/python-genai

class AiChatSession:
    """
    AI chat session that maintains conversation history and allows follow-up queries.
    """
    
    def __init__(
        self,
        model: str,
        schema: str,  # JSON5-formatted schema string
        retries: int = 1,
        backoff_seconds: int = 60,
    ):
        """
        Initialize an AI chat session.
        
        Args:
            model: Gemini 2.5 model identifier
            schema: JSON5-formatted schema string
            retries: Maximum retry attempts per request
            backoff_seconds: Delay between retries
        """
        self.model = model
        self.retries = retries
        self.backoff_seconds = backoff_seconds
        self.conversation_history: List[types.Content] = []
        self.parsed_schema = parse_and_validate_schema(schema)
        self.config = types.GenerateContentConfig(
            temperature=1,
            top_p=0.95,
            response_modalities=["TEXT"],
            responseMimeType="application/json",
            response_schema=self.parsed_schema,
            max_output_tokens=65536,
            safety_settings=[
                types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
                types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
            ],
        )

        if not model.startswith("gemini-2.5"):
            raise ValueError(f"Unsupported model: {model}")

    def send_message(self, prompt: str) -> str:
        """
        Send a message to the AI and get a response.
        
        Args:
            prompt: Input text prompt
            
        Returns:
            Generated text content as JSON string
        """

        response = self._generate_and_validate(prompt)
        
        # Add user message and AI response to conversation history
        self.conversation_history.append(
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        )
        self.conversation_history.append(
            types.Content(role="model", parts=[types.Part.from_text(text=response)])
        )
            
        return response
                

    def _generate_and_validate(self, prompt: str) -> str:
        """
        Generate content and ensure it matches the provided JSON Schema.
        """
        client = genai.Client(
            vertexai=True,
            project=python.gcp.PROJECT_ID,
            location=python.gcp.LOCATION
        )

        # Build contents including conversation history
        contents = self.conversation_history.copy()
        contents.append(
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        )



        result = ""
        
        for chunk in client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=self.config,
        ):
            if chunk.text:
                result += chunk.text

        cleaned = result.removeprefix("```json").removesuffix("```").strip()

        try:
            import jsonschema
            data = json.loads(cleaned)
            validator = jsonschema.Draft7Validator(self.parsed_schema)
            errors = list(validator.iter_errors(data))
            if errors:
                msgs = "; ".join(e.message for e in errors)
                raise ValueError(f"Response does not comply with schema: {msgs}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {e}")

        return cleaned

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """
        Get the conversation history as a list of dictionaries.
        
        Returns:
            List of conversation turns with role and content
        """
        history = []
        for content in self.conversation_history:
            text = ""
            for part in content.parts:
                if hasattr(part, 'text') and part.text:
                    text += part.text
            history.append({
                "role": content.role,
                "content": text
            })
        return history

    def clear_history(self):
        """Clear the conversation history."""
        self.conversation_history.clear()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass
