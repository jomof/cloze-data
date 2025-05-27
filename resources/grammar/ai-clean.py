#!/usr/bin/env python3
import yaml
import json
import argparse
from json_repair import repair_json
from python.aigen import aigen
from python.utils.build_cache.memoize.memoize import memoize_to_disk
import sys

def ai_clean(data, bazel_target):
    data = yaml.safe_load(data)

    prompt = """
You are a highly skilled Japanese teacher. You speak native Japanese that is natural and fluent. 
Though you are serious and terse, you love Japanese and you love to share the details, nuances, and beauty of the language and the culture with your students. 
As an INTJ, love to geek out on explaining Japanese grammar. But you never talk about MBTI in your lessons.
You are explaining a Japanese grammar point to a student.

A Japanese grammar point will appear between:
BEGIN_GRAMMAR_POINT_YAML
[input]
BEGIN_GRAMMAR_POINT_YAML
(Where [input] is the raw grammar point data you will be given.)

When you answer, do not wrap your output in code fences or additional commentary. Provide only valid JSON, which will be converted into YAML later.

Follow these rules:

0. If the grammar point contains a verb in **dictionary form** or adjective in **dictionary form**, add a new array field at the top, called "conjugations". It should list all of the possible conjugations of grammar_point, including the grammar point itself. 
   Only list conjugations that, when used, preserve the meaning of the grammar point. For example, if the grammar point is about the past, then don't list conjugations that aren't in the past.
   For example, if the grammar point was, then the array should be: dictionary (plain non-past): とみえる [commonly used], polite (non-past): とみえます [commonly used], negative (plain): とみえない [commonly used], negative (polite): とみえません [commonly used], past (plain): とみえた [commonly used], past (polite): とみえました [commonly used], negative past (plain): とみえなかった [commonly used], negative past (polite): とみえませんでした [commonly used], te-form: とみえて [rare in everyday speech], conditional (provisional ば-form): とみえれば [uncommon], conditional (tara-form): とみえたら [uncommon], volitional (plain): とみえよう [very rare], volitional (polite): とみえましょう [very rare], imperative (plain): とみえろ [unnatural], imperative (polite): とみえてください [unnatural], potential: とみえられる [rare], passive: とみえられる [rare], causative: とみえさせる [extremely unusual]
   Place this array immediately after the "grammar_point" field.
1. Do not modify the "grammar_point" text from [input]; output it exactly as provided.
   - You **must** add a "pronunciation" field, which contains:
      - "katakana" the grammar point in katakana.
      - "romaji" the "gramar_point" in romaji.
      - "pronunciation_warning" if needed only, explain why the romaji doesn't fully capture the pronunciation.
      - Example:
          "pronunciation": {
              "katakana": "テイルトコロダ",
              "romaji": "teiru tokoro da"
          },
1.2 You *must* add a 'formation' tag right under "grammar_point" that describes, in psuedo-algebraic notation, the formula for creating the grammar point from its component parts.
    For example, for the grammar point "見える", the formation could be:
    "formation": {
      "[Subject が] + 見える": "Indicates that something is visible or can be seen.",
      "[Object に] + [Subject が] + 見える": "Indicates how something appears to someone (it seems or looks a certain way).",
      "[Modifier] + 見える": "Adds nuance such as 'clearly visible,' 'looks small,' etc."
    }
2. Avoid Unicode escape sequences like \\u3051, just emit the Unicode.
3. If "meaning_warning" is empty or null, omit it entirely.
4. You **must** add an "etymology" field here that discusses the etymology of this grammar point.
5. The "writeup" field should:
    - Be primarily in English, supplemented by natural Japanese expressions as needed.
    - Incorporate essential details from the input while rephrasing for clarity.
    - Use markdown-style formatting (e.g., **important**).
    - Omit any example sentences here; examples go in the "examples" array.
    - Use double-quotes " for English quotes.
    - Refrain from quoting Japanese fragments such as なさい or なくてもいい.
    - You may include bullet points or sections like "Important Considerations" for clarity.
    - Don't mention the meaning_warning if there is one.
    - If the grammar point is primarily used by one gender, then mention that.
    - If the grammar point is primarily used by one age group, then mention that.
    - If the grammar point is primarily used in one region, then mention that.
6. Provide an "examples" array with multiple entries. Each should have:
    - Each example **must** use the grammar_point, though it may be in conjugated form.
      - If there are other conjugated forms of the grammar point that are commonly used, then some of the example sentences **must** include those conjugated forms.
    - "japanese": a natural-sounding Japanese sentence using this grammar point.
      - The "japanese" should have the grammar_point in **bold**.
    - "english": a natural-sounding English translation. Use quotes sparingly. Reserve them for when the grammar point can't be made without quotes.
    - "register": register of the sentence. One of: casual, formal, semi-formal, sonkeigo (respectful), kenjōgo (humble), teineigo (polite), shitashii kuchō (intimate), bijinesu nihongo (business), bungo (literary), hōgen (dialectical), surangu (slang), gun-go (military), wakamono kotoba (youth), meirei-kei no teineigo (polite imperative)
      - Example sentences **should** exhibit a wide variety of registers.
      - If possible, include one of the keigo registers in example sentences.
      - If possible, include a shitashii kuchō (intimate) example
    - "setting": setting of the sentence: One of: flirty, first-date, professional, academic, humorous, sarcastic, serious, persuasive, apologetic, informative, interrogative, storytelling, instructional, commanding, friendly, condescending, supportive, sympathetic, inspirational, intimate, negotiating, technical, legal, religious, creative, casual slang, emergency/alarm, reflective, optimistic, pessimistic, cautious, excited, melancholic
      - ** Don't invent new settings** Just use the list provided.
      - Example sentences should exhibit a wide variety of settings.
      - There should always be at least one flirty sentence. This teaches the learner to flirt.
      - There should always be at least one first-date sentence. This teaches the learner to date.
    - "conjugation": If the grammar point is conjugatable, then specify which congugation is used.
      - The content of this "conjugation" field must be taken from the top-level list of conjugations you generated earlier. Use the 'type' field.
      - Please include example sentences with a variety of conjugations, especially the ones encountered in common usage.
      - "conjugation" **must** be about the main grammar point and not other parts of the sentence. 
    - "speaker_gender": (optional) gender of the speaker. One of: male, female. **Use only if this sentence would typically only be spoken by this gender**
      - Example sentences should include at least one male and one female speaker_gender.
      - You *must not* embed hints about the speaker's gender in 'english' or 'japanese'. Put that here, in "speaker_gender".
    - "listener_gender": (optional) gender of the listener. One of: male, female (can omit if it doesn't matter in this sentence)
      - Example sentences should include at least one male and one female listener_gender.
       You *must not* embed hints about the listeners's gender in 'english' or 'japanese'. Put that here, in "listener_gender".
    - "speaker_age": (optional) One of: younger, older (can omit if it doesn't matter)
      - Example sentences should include at least one younger and one older speaker_age.
    - "listener_age": (optional) One of: younger, older (can omit if it doesn't matter)
      - Example sentences should include at least one younger and one older listener_age.
    - "nuance":  Explain, in English with Japanese references to the sentence, how this sentence exhibits the interplay between the "speaker_age" vs "listener_age", "speaker_gender" vs "listener_gender", why the "register" applies.
      - If there is a "speaker_gender", then "nuance" **must** mention the specific Japanese, in 「quotes」, that would only be spoken by that gender. 
      - Nuance **must** refer to parts of the japanese sentence in 「quotes」.
    - "etymology": If there is something etymologically interesting in the Japanese sentence, then mention it here in English.
    - You *must not*
        
7. At least one example should include a flirty innuendo. It should be phrased as the speaker (male or female) flirting with the listener (female or male).
8. At least one example should suit an early romantic or first-meeting context (without using the word "date"). It should be phrased as the speaker (male or female) flirting with the listener (female or male).
9. If the input examples contain dialogue (A: ... B: ...), rewrite them into single-sentence statements that preserve the lesson but remove direct dialogue format.
10. Prefer simpler sentences that are still natural and convey the grammar point. Strongly prefer not using quotes. Reserve quotes for when the grammar point needs them.
11. Order examples from simpler to more advanced usage.
12. For English contractions, use a single apostrophe ' (e.g., "don't").
13. You may include a "post_example_writeup" section after "examples" if more clarification is helpful, but don't reference examples by any numeric label.
14. If "false_friends" are present, each entry should have:
    - "false_friend": the term.
    - "nuance": a concise contrast to the main grammar point (e.g., "Unlike [grammar_point], [false_friend]...").
15. You may add a "post_false_friends_writeup" to clarify further differences between the grammar point and these similar expressions. Do not call them "false friends" in that section—just provide a short explanation of how to avoid mixing them up.
16. You may fix minor inaccuracies in "details", but do not invent new details.
17. Ensure the JSON is valid and properly escaped for YAML conversion. Avoid additional formatting or code fences.
18. Japanese sentences should not have furigana text embedded. 
19. There should just be one english sentence per example. Don't make multiple sentences.

** Template of the Expected Output JSON **
Below is a minimal template demonstrating how the final JSON structure should look. You will output something like this, without code fences:

```
{
    "grammar_point": "...",
    "id": "gp0001",
    "rank": 5,
    "conjugations": [
        { type: "dictionary form",
          form: "とみえる",
          rarity: "common"
        },
        // etc.
    ],
    "jlpt": "...",
    "meaning": "...", // English
    "meaning_warning": "...", // English
    "details": {
        "Register": "...",
        // etc
    },
    "writeup": "...", // English
    "examples": [
        {
            "japanese": "晩ご飯を食べて歯を磨いた。", // Japanese
            "english": "I ate dinner and brushed my teeth.", // English
            "conjugation": "dictionary form", // From top-level conjugation 'types'
            "register": "...", // Required
            "setting": "...", // Required
            "speaker_gender": "...", // Only if required for the sentence
            "listener_gender": "...", // Only if required for the sentence
            "speaker_age": "...", // Only if required for the sentence
            "listener_age": "...", // Only if required for the sentence
            "nuance": "..." // English
        },
        // etc
    ],
    "post_example_writeup": "", // English
    "false_friends": [
        {
            "term": "...",
            "meaning": "...",
            "kind": "...",
            "nuance": "" // English
        },
        // etc
    ],
    "post_false_friends_writeup": "..." // English
}```
    - If "meaning_warning" is null or empty, you omit it entirely.
    - The same goes for "false_friends", "post_example_writeup", and "post_false_friends_writeup" if they do not apply.
    - Make sure the 'rank' field is second after 'grammar_point' in the output JSON.

Here are the kanji learned at each JLPT level:
    JLPT Kanji N5, 人, 一, 日, 大, 年, 出, 本, 中, 子, 見, 国, 上, 分, 生, 行, 二, 間, 時, 気, 十, 女, 三, 前, 入, 小, 後, 長, 下, 学, 月, 何, 来, 話, 山, 高, 今, 書, 五, 名, 金, 男, 外, 四, 先, 川, 東, 聞, 語, 九, 食, 八, 水, 天, 木, 六, 万, 白, 七, 円, 電, 父, 北, 車, 母, 半, 百, 土, 西, 読, 千, 校, 右, 南, 左, 友, 火, 毎, 雨, 休, 午, , 
    JLPT Kanji N4, 言, 手, 自, 者, 事, 思, 会, 家, 的, 方, 地, 目, 場, 代, 私, 立, 物, 田, 体, 動, 社, 知, 理, 同, 心, 発, 作, 新, 世, 度, 明, 力, 意, 用, 主, 通, 文, 屋, 業, 持, 道, 身, 不, 口, 多, 野, 考, 開, 教, 近, 以, 問, 正, 真, 味, 界, 無, 少, 海, 切, 重, 集, 員, 公, 画, 死, 安, 親, 強, 使, 朝, 題, 仕, 京, 足, 品, 着, 別, 音, 元, 特, 風, 夜, 空, 有, 起, 運, 料, 楽, 色, 帰, 歩, 悪, 広, 店, 町, 住, 売, 待, 古, 始, 終, 計, 院, 送, 族, 映, 買, 病, 早, 質, 台, 室, 可, 建, 転, 医, 止, 字, 工, 急, 図, 黒, 花, 英, 走, 青, 答, 紙, 歌, 注, 赤, 春, 館, 旅, 験, 写, 去, 研, 飲, 肉, 服, 銀, 茶, 究, 洋, 兄, 秋, 堂, 週, 習, 試, 夏, 弟, 鳥, 犬, 夕, 魚, 借, 飯, 駅, 昼, 冬, 姉, 曜, 漢, 牛, 妹, 貸, 勉, , 
    JLPT Kanji N3, 合, 部, 彼, 内, 実, 当, 戦, 性, 対, 関, 感, 定, 政, 取, 所, 現, 最, 化, 民, 相, 法, 全, 情, 向, 平, 成, 経, 信, 面, 連, 原, 顔, 機, 次, 数, 美, 回, 表, 声, 報, 要, 変, 神, 記, 和, 引, 治, 決, 太, 込, 受, 解, 市, 期, 様, 活, 頭, 組, 指, 説, 能, 葉, 流, 然, 初, 在, 調, 笑, 議, 直, 夫, 選, 権, 利, 制, 続, 石, 進, 伝, 加, 助, 点, 産, 務, 件, 命, 番, 落, 付, 得, 好, 違, 殺, 置, 返, 論, 際, 歳, 反, 形, 光, 首, 勝, 必, 係, 由, 愛, 都, 放, 確, 過, 約, 馬, 状, 想, 官, 交, 米, 配, 若, 資, 常, 果, 呼, 共, 残, 判, 役, 他, 術, 支, 両, 乗, 済, 供, 格, 打, 御, 断, 式, 師, 告, 深, 存, 争, 覚, 側, 飛, 参, 突, 容, 育, 構, 認, 位, 達, 守, 満, 消, 任, 居, 予, 路, 座, 客, 船, 追, 背, 観, 誰, 息, 失, 老, 良, 示, 号, 職, 王, 識, 警, 優, 投, 局, 難, 種, 念, 寄, 商, 害, 頼, 横, 増, 差, 苦, 収, 段, 俺, 渡, 与, 演, 備, 申, 例, 働, 景, 抜, 遠, 絶, 負, 福, 球, 酒, 君, 察, 望, 婚, 単, 押, 割, 限, 戻, 科, 求, 談, 降, 妻, 岡, 熱, 浮, 等, 末, 幸, 草, 越, 登, 類, 未, 規, 精, 抱, 労, 処, 退, 費, 非, 喜, 娘, 逃, 探, 犯, 薬, 園, 疑, 緒, 静, 具, 席, 速, 舞, 宿, 程, 倒, 寝, 宅, 絵, 破, 庭, 婦, 余, 訪, 冷, 暮, 腹, 危, 許, 似, 険, 財, 遊, 雑, 恐, 値, 暗, 積, 夢, 痛, 富, 刻, 鳴, 欲, 途, 曲, 耳, 完, 願, 罪, 陽, 亡, 散, 掛, 昨, 怒, 留, 礼, 列, 雪, 払, 給, 敗, 捕, 忘, 晴, 因, 折, 迎, 悲, 港, 責, 除, 困, 閉, 吸, 髪, 束, 眠, 易, 窓, 祖, 勤, 昔, 便, 適, 吹, 候, 怖, 辞, 否, 遅, 煙, 徒, 欠, 迷, 洗, 互, 才, 更, 歯, 盗, 慣, 晩, 箱, 到, 頂, 杯, 皆, 招, 寒, 恥, 疲, 貧, 猫, 誤, 努, 幾, 賛, 偶, 忙, 泳, 靴, 偉, , 
    JLPT Kanji N2, 軍, 兵, 島, 村, 門, 戸, 武, 城, 総, 団, 線, 設, 勢, 党, 史, 営, 府, 巻, 介, 蔵, 造, 根, 寺, 査, 将, 改, 県, 泉, 像, 細, 谷, 奥, 再, 血, 算, 象, 清, 技, 州, 領, 橋, 芸, 型, 香, 量, 久, 境, 階, 区, 波, 移, 域, 周, 接, 鉄, 頃, 材, 個, 協, 各, 帯, 歴, 編, 裏, 比, 坂, 装, 省, 税, 競, 囲, 辺, 河, 極, 防, 低, 林, 導, 森, 丸, 胸, 陸, 療, 諸, 管, 仲, 革, 担, 効, 賞, 星, 復, 片, 並, 底, 温, 軽, 録, 腰, 著, 乱, 章, 殿, 布, 角, 仏, 永, 誌, 減, 略, 準, 委, 令, 刊, 焼, 里, 圧, 額, 印, 池, 臣, 庫, 農, 板, 恋, 羽, 専, 逆, 腕, 短, 普, 岩, 竹, 児, 毛, 版, 宇, 況, 被, 岸, 超, 豊, 含, 植, 補, 暴, 課, 跡, 触, 玉, 震, 億, 肩, 劇, 刺, 述, 輪, 浅, 純, 薄, 阪, 韓, 固, 巨, 講, 般, 湯, 捨, 衣, 替, 央, 骨, 齢, 照, 層, 弱, 築, 脳, 航, 快, 翌, 旧, 筆, 換, 群, 爆, 捜, 油, 叫, 伸, 承, 雲, 練, 紹, 包, 庁, 測, 占, 混, 倍, 乳, 荒, 詰, 栄, 床, 則, 禁, 順, 枚, 厚, 皮, 輸, 濃, 簡, 孫, 丈, 黄, 届, 絡, 採, 傾, 鼻, 宝, 患, 延, 律, 希, 甘, 湾, 沈, 販, 欧, 砂, 尊, 紅, 複, 泊, 荷, 枝, 依, 幼, 斬, 勇, 昇, 寿, 菜, 季, 液, 券, 祭, 袋, 燃, 毒, 札, 狙, 脇, 卒, 副, 敬, 針, 拝, 浴, 悩, 汚, 灯, 坊, 尻, 涙, 停, 了, 汗, 郵, 幅, 童, 虫, 埋, 舟, 闇, 棒, 貨, 肌, 臓, 塩, 均, 湖, 損, 膝, 辛, 双, 軒, 績, 干, 姓, 掘, 籍, 珍, 訓, 預, 署, 漁, 緑, 畳, 咲, 貿, 踊, 封, 兆, 柱, 駐, 祝, 炭, 柔, 雇, 乾, 鋭, 氷, 隅, 冊, 糸, 募, 硬, 塗, 憎, 泥, 脂, 粉, 詞, 筒, 掃, 塔, 賢, 拾, 麦, 刷, 卵, 械, 皿, 祈, 灰, 召, 溶, 磨, 粒, 喫, 机, 貯, 匹, 綿, 贈, 凍, 瓶, 帽, 涼, 秒, 湿, 蒸, 菓, 耕, 鉱, 膚, 胃, 挟, 郊, 銅, 鈍, 貝, 缶, 枯, 滴, 符, 畜, 軟, 濯, 隻, 伺, 沸, 曇, 肯, 燥, 零, , 
    JLPT Kanji N1, 郎, 結, 氏, 衛, 第, 保, 義, 吉, 士, 藤, 井, 江, 張, 松, 応, 視, 態, 姿, 皇, 宮, 離, 基, 隊, 素, 価, 撃, 振, 証, 派, 僕, 佐, 紀, 統, 器, 異, 護, 条, 独, 源, 影, 眼, 企, 津, 案, 策, 宗, 提, 昭, 密, 司, 検, 康, 沢, 秀, 興, 率, 評, 監, 崎, 鮮, 激, 徳, 挙, 志, 敷, 系, 織, 製, 端, 遺, 房, 街, 尾, 株, 従, 敵, 展, 描, 修, 我, 載, 響, 秘, 攻, 健, 裁, 隠, 環, 援, 故, 幕, 督, 倉, 施, 嫌, 継, 障, 貴, 整, 衆, 及, 盛, 玄, 恵, 授, 弾, 養, 驚, 奈, 推, 樹, 為, 雄, 刀, 弁, 妙, 模, 抗, 級, 瞬, 称, 華, 傷, 闘, 筋, 訳, 射, 善, 黙, 柄, 刑, 節, 脱, 厳, 博, 陣, 奇, 忠, 染, 微, 標, 縁, 壁, 駆, 麻, 甲, 藩, 迫, 踏, 討, 聖, 典, 剣, 症, 納, 弥, 融, 浜, 郷, 惑, 柳, 拠, 奉, 壊, 益, 句, 属, 功, 帝, 賀, 堀, 創, 泣, 憶, 幹, 露, 矢, 握, 儀, 聴, 襲, 徴, 丁, 憲, 閣, 救, 陰, 繰, 那, 操, 騒, 己, 魔, 撮, 携, 隣, 宣, 遣, 訴, 茂, 釣, 批, 誘, 核, 哲, 豪, 締, 鹿, 就, 滅, 仰, 瀬, 致, 伏, 杉, 審, 避, 揺, 浦, 至, 裕, 盟, 執, 崩, 鬼, 酸, 拡, 銃, 維, 縄, 詩, 廃, 充, 鏡, 仮, 吐, 請, 眺, 沖, 躍, 威, 屈, 勘, 徹, 斎, 謝, 艦, 催, 舎, 仁, 衝, 脚, 虎, 潮, 穴, 怪, 仙, 輝, 緊, 唇, 忍, 狂, 奪, 診, 竜, 債, 鈴, 僧, 掲, 伯, 熊, 浪, 梅, 看, 俊, 摘, 項, 霊, 垣, 慢, 扱, 渉, 如, 縮, 詳, 旦, 慮, 雅, 砲, 謀, 懐, 愚, 舌, 駄, 奴, 豆, 又, 銭, 抑, 侍, 宙, 範, 潜, 酔, 呂, 還, 丹, 亜, 亀, 沼, 巡, 臭, 慶, 距, 釈, 侵, 僚, 悟, 隆, 裂, 尋, 旗, 羅, 揮, 票, 稲, 胞, 懸, 稿, 塚, 盤, 災, 曹, 尽, 嫁, 繁, 即, 帳, 飾, 沿, 獲, 伴, 唐, 狭, 添, 剤, 魅, 契, 邪, 挑, 免, 爵, 択, 廊, 析, 輩, 敏, 鶴, 虚, 往, 趣, 烈, 索, 匂, 摩, 菊, 滑, 沙, 裸, 孝, 綱, 邸, 邦, 揚, 卓, 騎, 墓, 姫, 孔, 耐, 須, 臨, 献, 脈, 芝, 唱, 亭, 誕, 貫, 偽, 奮, 桜, 熟, 排, 透, 棄, 削, 奏, 幻, 麗, 逮, 誠, 炎, 椅, 寛, 斉, 穂, 兼, 飼, 促, 尚, 彩, 暖, 俗, 較, 傍, 肝, 畑, 峰, 抵, 恩, 誇, 網, 渋, 魂, 牧, 控, 紛, 戒, 没, 既, 股, 脅, 征, 覆, 郡, 丘, 佳, 叔, 託, 哀, 肥, 朗, 慎, 悠, 眉, 拒, 概, 顧, 腐, 挨, 孤, 拶, 却, 賊, 荘, 匠, 悔, 獄, 滞, 遇, 淡, 購, 併, 崇, 唯, 垂, 岐, 俳, 斜, 嬢, 陥, 償, 鑑, 勧, 葬, 焦, 剛, 膨, 廷, 紫, 銘, 鎌, 菌, 稼, 譲, 随, 猛, 遂, 冒, 泰, 翼, 凄, 序, 扉, 是, 寸, 賃, 偵, 澄, 殊, 緩, 頑, 紋, 糖, 煮, 芳, 惨, 歓, 虐, 喉, 旨, 凝, 圏, 拭, 涯, 貞, 堅, 倫, 壇, 呉, 暇, 貌, 塞, 噴, 婆, 岳, 蹴, 鍵, 膳, 尺, 罰, 漏, 朱, 覧, 漂, 汁, 寂, 嘆, 禅, 浄, 酷, 刃, 漫, 霧, 暑, 棚, 袖, 壮, 旬, 彫, 需, 鎖, 潰, 縦, 粧, 慌, 穏, 枠, 謎, 誉, 逸, 駒, 惜, 措, 晶, 琴, 摂, 拍, 稽, 礎, 遭, 掌, 鍋, 弓, 克, 据, 胆, 跳, 縛, 鎮, 雷, 恨, 顕, 殖, 寧, 湧, 棋, 巧, 浸, 桃, 隔, 班, 甚, 妊, 祉, 獣, 疾, 塾, 潟, 撲, 塊, 絞, 履, 苗, 芋, 冗, 陶, 励, 陳, 猿, 葛, 傘, 啓, 劣, 撤, 殴, 盾, 衰, 滝, 慰, 蛇, 梨, 癖, 潤, 鉢, 戯, 腸, 偏, 巣, 宴, 炉, 棟, 洞, 狩, 陛, 磁, 潔, 膜, 乏, 祥, 曽, 舗, 抽, 睡, 賭, 括, 貢, 犠, 粗, 卑, 貼, 拉, 牲, 帆, 挿, 翻, 羊, 枕, 錯, 謙, 珠, 蓄, 拓, 鼓, 粋, 尉, 后, 粘, 披, 徐, 悦, 堪, 冠, 愉, 尿, 顎, 誓, 憂, 簿, 糧, 架, 芽, 軸, 苛, 蓋, 盆, 凶, 妃, 庶, 秩, 裾, 幽, 凡, 漠, 拙, 恒, 暦, 腫, 峠, 宰, 蛮, 窮, 擦, 爪, 稚, 辱, 嵐, 憤, 癒, 鬱, 疎, 雰, 彰, 肺, 傑, 拘, 頻, 緯, 妖, 豚, 藍, 矛, 鍛, 繊, 縫, 把, 楼, 捉, 漬, 紳, 飽, 宛, 閥, 旋, 坪, 崖, 叱, 鶏, 峡, 溝, 朴, 軌, 瓦, 喪, 墨, 疫, 遍, 濁, 扇, 拳, 乙, 酵, 堤, 阻, 桑, 虜, 乞, 恭, 鐘, 剰, 慈, 径, 培, 擁, 郭, 呪, 砕, 汰, 勃, 翁, 絹, 譜, 陵, 痴, 笛, 昧, 訟, 唾, 肪, 塀, 碁, 敢, 塁, 暁, 胴, 謡, 飢, 欄, 艶, 痕, 怠, 欺, 弦, 泡, 諦, 伐, 餅, 寮, 厄, 奔, 瞳, 昆, 椎, 懇, 唄, 渦, 襟, 吟, 覇, 衡, 呈, 隙, 淫, 娠, 循, 懲, 錦, 猟, 幣, 附, 箇, 醜, 箸, 戚, 喚, 紺, 某, 鋼, 褒, 赴, 媒, 妬, 遮, 窯, 侯, 釜, 茎, 蔑, 嗅, 壌, 蜜, 尼, 肢, 赦, 酬, 戴, 詠, 斗, 宜, 殻, 墳, 炊, 碑, 痩, 但, 奨, 践, 滋, 儒, 薦, 怨, 栽, 刈, 閑, 錠, 扶, 妥, 妨, 醒, 詣, 胎, 窟, 巾, 蜂, 忌, 骸, 弄, 嫉, 粛, 罵, 囚, 鉛, 搭, 諭, 璧, 阜, 喝, 享, 騰, 嗣, 勅, 篤, 勲, 埼, 伎, 曖, 詐, 餌, 岬, 暫, 爽, 肖, 詮, 諾, 柿, 芯, 綻, 訂, 汽, 薫, 隷, 俵, 遷, 枢, 肘, 麓, 憧, 帥, 漆, 酌, 頓, 賠, 渇, 慕, 婿, 妄, 慨, 匿, 渓, 侮, 髄, 穀, 薪, 轄, 洪, 牙, 咽, 迅, 該, 逐, 嘲, 墜, 臆, 餓, 挫, 錬, 桟, 溺, 賄, 盲, 鯨, 侶, 艇, 丼, 堕, 瘍, 槽, 憩, 僅, 閲, 柵, 畔, 睦, 唆, 悼, 吏, 穫, 酢, 賜, 腎, 梗, 瑠, 羨, 搬, 剖, 酎, 畿, 宵, 拐, 醸, 猶, 諮, 畏, 泌, 愁, 逝, 朽, 硫, 瞭, 擬, 叙, 弊, 累, 煩, 踪, 藻, 蚊, 栃, 且, 鋳, 蔽, 茨, 棺, 慄, 傲, 硝, 舶, 租, 倣, 謹, 抹, 虹, 捻, 娯, 臼, 喩, 萎, 蛍, 窒, 腺, 桁, 玩, 冶, 羞, 栓, 惧, 寡, 畝, 淑, 嫡, 屯, 糾, 遡, 陪, 雌, 舷, 霜, 殉, 紡, 貪, 庸, 韻, 繕, 搾, 刹, 采, 堆, 禍, 煎, 姻, 斑, 冥, 抄, 拷, 遜, 旺, 准, 勾, 廉, 礁, 壱, 麺, 升, 卸, 耗, 謁, 璃, 坑, 串, 弔, 賓, 塡, 痢, 嚇, 濫, 俸, 箋, 凸, 脊, 詔, 緻, 凹, 罷, 漸, 賦, 弧, 褐, 辣, 摯, 汎, 斥, 厘, 矯, 毀, 窃, 遵, 賂, 惰, 蚕, 氾, 諧, 倹, 款, 媛, 憾, 哺, 衷, 彙, 迭, 嘱, 恣, 墾, 逓, 劾, 酪, 沃, 塑, 痘, 憬, 朕, 虞, 丙, 斤, 捗, 弐, 訃, 謄, 繭, 璽, 頒, 楷, 剥, 籠, 錮, 頰
Example sentences should use kanji appropriate for the JLPT level of the grammar point. So, for example, if the grammar point is JLPT N3, the example sentences should use kanji from the N3, N4, and N5 lists. 

BEGIN_GRAMMAR_POINT_YAML
[input_replace]
BEGIN_GRAMMAR_POINT_YAML

Once you have the JSON content in mind, please do the following steps and make corrections as needed:
1. Are the sections that require English as the main language actually in English? Those sections are "writeup", "nuance", "meaning", "meaning_warning", "etymology".
2. See #1 above and look again. These fields *must* have English as the main language.
3. If somehow, you still failed to make those sections English, then apologize (mentally) and fix them.
4. Make sure there are no A/B dialog style example sentences. They should be full sentences.
5. If the grammar_point is something conjugatable, like a verb, do the example sentences demonstrate the different conjugations?
6. Did you change the grammar_point value? If so, chide yourself thoroughly, and set grammar_point to its original value.

That is all.
""".replace("[input_replace]", json.dumps(data, ensure_ascii=False, indent=4))

    grammar_point_name = data["grammar_point"]
    id = data["id"]
    rank = data["rank"]
    print(f"Processing grammar point: {grammar_point_name} (Rank: {rank})")
    response = memoize_to_disk(bazel_target, aigen, prompt, "gemini-2.0-flash-001")
    #response = memoize_to_disk(bazel_target, aigen, prompt, "gemini-2.0-flash-thinking-exp-1219")
    response = response.removeprefix("```json").removesuffix("\n").removesuffix("```")
    response = repair_json(response)
    json_response = json.loads(response)
    json_response["id"] = id
    json_response["rank"] = rank
    
    # response = yaml.dumps(response, ensure_ascii=False, indent=4)

    if grammar_point_name != json_response["grammar_point"]:
        raise Exception(f"Grammar point mismatch: {data['grammar_point']} != {json_response['grammar_point']}")

    return json.dumps(json_response, ensure_ascii=False, indent=4)

def main(input_file, output_file, bazel_target):
    with open(input_file, 'r', encoding='utf-8') as file:
        data = file.read()
    result = ai_clean(data, bazel_target)

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(result)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, help='Input file path')
    parser.add_argument('--destination', required=True, help='Output file path')
    parser.add_argument('--bazel-target', required=True, help='Name of the bazel target')
    args = parser.parse_args()
    main(args.source, args.destination, args.bazel_target)
