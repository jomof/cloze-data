from typing import Any, Callable, Dict, List, Tuple, Union

JsonValue = Union[Dict[str, Any], List[Any], str, int, float, bool, None]


def preprocess_schema(schema: Dict[str, Any]) -> Dict[str, List[Tuple[Dict[str, Any], str]]]:
    """
    Precompute alias chains for definitions.
    Returns a mapping from definition name to list of (schema_node, type_name) alias chain.
    """
    definitions = schema.get("definitions", {})
    # Map definition name -> schema node for quick lookup
    ref_map: Dict[str, Dict[str, Any]] = {}
    for name, node in definitions.items():
        if isinstance(node, dict):
            ref_map[name] = node

    # Build alias chains: definition name -> list of (schema_node, type_name)
    alias_chain_cache: Dict[str, List[Tuple[Dict[str, Any], str]]] = {}

    for def_name, node in ref_map.items():
        chain: List[Tuple[Dict[str, Any], str]] = []
        visited: set = set()
        current = node
        # First, include the definition itself as specific alias
        chain.append((current, def_name))
        visited.add(def_name)
        # Then follow any nested $ref until reaching a non-$ref schema
        while isinstance(current, dict) and "$ref" in current:
            ref_str = current.get("$ref")
            if not isinstance(ref_str, str) or not ref_str.startswith("#/definitions/"):
                break
            target_name = ref_str.rsplit("/", 1)[-1]
            if target_name in visited:
                # Circular reference detected
                break
            visited.add(target_name)
            target_schema = ref_map.get(target_name)
            if not isinstance(target_schema, dict):
                break
            chain.append((target_schema, target_name))
            current = target_schema
        alias_chain_cache[def_name] = chain

    return alias_chain_cache


def visit_json(
    obj: JsonValue,
    schema: Dict[str, Any],
    fn: Callable[[JsonValue, Union[str, None], str], Union[JsonValue, None]]
) -> JsonValue:
    """
    Traverse `obj` according to `schema`, calling fn(value, type_name, path) at each node.
    """
    alias_chain_cache = preprocess_schema(schema)

    def segments_to_string(segments: List[Tuple[str, Union[str, int]]]) -> str:
        if not segments:
            return ''
        parts: List[str] = []
        for stype, key in segments:
            if stype == 'prop':
                if parts:
                    parts.append('.')
                parts.append(str(key))
            else:  # 'idx'
                parts.append(f'[{key}]')
        return ''.join(parts)

    def _visit(
        value: JsonValue,
        subschema: Any,
        path_segments: List[Tuple[str, Union[str, int]]],
        inherited_prefix: Union[str, None] = None,
        skip_fn: bool = False
    ) -> JsonValue:
        # 1) Quick check for $ref
        if isinstance(subschema, dict):
            ref_str = subschema.get("$ref")
        else:
            ref_str = None
        if isinstance(ref_str, str) and ref_str.startswith("#/definitions/"):
            target_name = ref_str.rsplit("/", 1)[-1]
            chain = alias_chain_cache.get(target_name, [])
            # Call fn on each alias in reverse (most general -> most specific)
            path_str = segments_to_string(path_segments)
            current_value = value
            for schema_node, tn in reversed(chain):
                replacement = fn(current_value, tn, path_str)
                if replacement is not None:
                    current_value = replacement
            # Descend into the most general schema node, skipping fn there
            if chain:
                most_general_schema = chain[-1][0]
                return _visit(current_value, most_general_schema, path_segments, inherited_prefix=None, skip_fn=True)
            return current_value

        # 2) Inline type name by inherited_prefix and subschema type
        if isinstance(subschema, dict):
            stype = subschema.get('type')
            if inherited_prefix and isinstance(stype, str):
                type_name = f"{inherited_prefix}/{stype}"
            else:
                type_name = inherited_prefix
        else:
            type_name = None
        # 3) Call fn if not skipped
        current_value = value
        if not skip_fn:
            path_str = segments_to_string(path_segments)
            replacement = fn(current_value, type_name, path_str)
            if replacement is not None:
                current_value = replacement

        # 4) Descend based on type: object, array, or primitive
        if isinstance(subschema, dict):
            schema_type = subschema.get('type')
        else:
            schema_type = None
        # 4.a) Object: recurse into properties
        if schema_type == 'object' and isinstance(current_value, dict):
            props = subschema.get('properties')
            if isinstance(props, dict):
                for key, child_schema in props.items():
                    if key in current_value:
                        new_segments = path_segments + [('prop', key)]
                        new_val = _visit(current_value[key], child_schema, new_segments, inherited_prefix=key, skip_fn=False)
                        if new_val is not current_value[key]:
                            current_value[key] = new_val  # type: ignore
        # 4.b) Array: recurse into items
        elif schema_type == 'array' and isinstance(current_value, list):
            item_schema = subschema.get('items')
            if item_schema is not None:
                for idx, item in enumerate(current_value):
                    new_segments = path_segments + [('idx', idx)]
                    new_item = _visit(item, item_schema, new_segments, inherited_prefix=inherited_prefix, skip_fn=False)
                    if new_item is not item:
                        current_value[idx] = new_item  # type: ignore
        # 4.c) Primitives: nothing to do
        return current_value

    return _visit(obj, schema, path_segments=[], inherited_prefix=None, skip_fn=False)
