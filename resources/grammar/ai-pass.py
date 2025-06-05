#!/usr/bin/env python3
import yaml
import json
from python.ai import aigen
from python.utils.build_cache.memoize.memoize import memoize_to_disk
import os
import textwrap
from python.grammar import clean_lint, GRAMMAR_SCHEMA_WITH_COMMENTS
from python.mapreduce import MapReduce
import asyncio
import sys
import json
from json_repair import repair_json

def ws(s: str) -> str:
    return "\n".join(line.strip() for line in s.splitlines())

PERSONA = ws("""
        You are a highly skilled Japanese teacher. You speak native Japanese that is natural and fluent. 
        Though you are typically serious and terse, you're also warm and empathetic.
        You're conscientious about gender, race, disability, and other forms of diversity, and you are careful to avoid stereotypes,
        but you won't avoid discussing cultural differences when they are relevant to the topic at hand.
        You love Japanese and you love to share the details, history, nuances, and beauty of the language and the culture with your students.
        As an ENTJ, love to geek out on explaining Japanese grammar. But you never talk about MBTI in your lessons.
    """) 

AUDIENCE = ws("""
        ** -Audience- **                
        You are explaining a Japanese grammar point to a student whose first language is American English.
        They are very curious about grammatic details and will often ask you questions about how certain 
        phrases came about historically.
    """) 
OUTPUT_SCHEMA = textwrap.dedent("""
        ** -Output Schema- **
        Below is a minimal template demonstrating how the final JSON structure should look. You will output something with this schema, without code fences.
        Comments in the schema are instructions for you that use *MUST* follow. These comments will apply to the schema element that follows them.

        BEGIN OUTPUT_SCHEMA
        [grammar_schema]
        END OUTPUT_SCHEMA
    """).replace("[grammar_schema]", GRAMMAR_SCHEMA_WITH_COMMENTS)
KANJI_BY_LEVEL = ws("""
        ** -Kanji by JLPT level- **
        Here are the kanji learned at each JLPT level:
            JLPT Kanji N5, 人, 一, 日, 大, 年, 出, 本, 中, 子, 見, 国, 上, 分, 生, 行, 二, 間, 時, 気, 十, 女, 三, 前, 入, 小, 後, 長, 下, 学, 月, 何, 来, 話, 山, 高, 今, 書, 五, 名, 金, 男, 外, 四, 先, 川, 東, 聞, 語, 九, 食, 八, 水, 天, 木, 六, 万, 白, 七, 円, 電, 父, 北, 車, 母, 半, 百, 土, 西, 読, 千, 校, 右, 南, 左, 友, 火, 毎, 雨, 休, 午, , 
            JLPT Kanji N4, 言, 手, 自, 者, 事, 思, 会, 家, 的, 方, 地, 目, 場, 代, 私, 立, 物, 田, 体, 動, 社, 知, 理, 同, 心, 発, 作, 新, 世, 度, 明, 力, 意, 用, 主, 通, 文, 屋, 業, 持, 道, 身, 不, 口, 多, 野, 考, 開, 教, 近, 以, 問, 正, 真, 味, 界, 無, 少, 海, 切, 重, 集, 員, 公, 画, 死, 安, 親, 強, 使, 朝, 題, 仕, 京, 足, 品, 着, 別, 音, 元, 特, 風, 夜, 空, 有, 起, 運, 料, 楽, 色, 帰, 歩, 悪, 広, 店, 町, 住, 売, 待, 古, 始, 終, 計, 院, 送, 族, 映, 買, 病, 早, 質, 台, 室, 可, 建, 転, 医, 止, 字, 工, 急, 図, 黒, 花, 英, 走, 青, 答, 紙, 歌, 注, 赤, 春, 館, 旅, 験, 写, 去, 研, 飲, 肉, 服, 銀, 茶, 究, 洋, 兄, 秋, 堂, 週, 習, 試, 夏, 弟, 鳥, 犬, 夕, 魚, 借, 飯, 駅, 昼, 冬, 姉, 曜, 漢, 牛, 妹, 貸, 勉, , 
            JLPT Kanji N3, 合, 部, 彼, 内, 実, 当, 戦, 性, 対, 関, 感, 定, 政, 取, 所, 現, 最, 化, 民, 相, 法, 全, 情, 向, 平, 成, 経, 信, 面, 連, 原, 顔, 機, 次, 数, 美, 回, 表, 声, 報, 要, 変, 神, 記, 和, 引, 治, 決, 太, 込, 受, 解, 市, 期, 様, 活, 頭, 組, 指, 説, 能, 葉, 流, 然, 初, 在, 調, 笑, 議, 直, 夫, 選, 権, 利, 制, 続, 石, 進, 伝, 加, 助, 点, 産, 務, 件, 命, 番, 落, 付, 得, 好, 違, 殺, 置, 返, 論, 際, 歳, 反, 形, 光, 首, 勝, 必, 係, 由, 愛, 都, 放, 確, 過, 約, 馬, 状, 想, 官, 交, 米, 配, 若, 資, 常, 果, 呼, 共, 残, 判, 役, 他, 術, 支, 両, 乗, 済, 供, 格, 打, 御, 断, 式, 師, 告, 深, 存, 争, 覚, 側, 飛, 参, 突, 容, 育, 構, 認, 位, 達, 守, 満, 消, 任, 居, 予, 路, 座, 客, 船, 追, 背, 観, 誰, 息, 失, 老, 良, 示, 号, 職, 王, 識, 警, 優, 投, 局, 難, 種, 念, 寄, 商, 害, 頼, 横, 増, 差, 苦, 収, 段, 俺, 渡, 与, 演, 備, 申, 例, 働, 景, 抜, 遠, 絶, 負, 福, 球, 酒, 君, 察, 望, 婚, 単, 押, 割, 限, 戻, 科, 求, 談, 降, 妻, 岡, 熱, 浮, 等, 末, 幸, 草, 越, 登, 類, 未, 規, 精, 抱, 労, 処, 退, 費, 非, 喜, 娘, 逃, 探, 犯, 薬, 園, 疑, 緒, 静, 具, 席, 速, 舞, 宿, 程, 倒, 寝, 宅, 絵, 破, 庭, 婦, 余, 訪, 冷, 暮, 腹, 危, 許, 似, 険, 財, 遊, 雑, 恐, 値, 暗, 積, 夢, 痛, 富, 刻, 鳴, 欲, 途, 曲, 耳, 完, 願, 罪, 陽, 亡, 散, 掛, 昨, 怒, 留, 礼, 列, 雪, 払, 給, 敗, 捕, 忘, 晴, 因, 折, 迎, 悲, 港, 責, 除, 困, 閉, 吸, 髪, 束, 眠, 易, 窓, 祖, 勤, 昔, 便, 適, 吹, 候, 怖, 辞, 否, 遅, 煙, 徒, 欠, 迷, 洗, 互, 才, 更, 歯, 盗, 慣, 晩, 箱, 到, 頂, 杯, 皆, 招, 寒, 恥, 疲, 貧, 猫, 誤, 努, 幾, 賛, 偶, 忙, 泳, 靴, 偉, , 
            JLPT Kanji N2, 軍, 兵, 島, 村, 門, 戸, 武, 城, 総, 団, 線, 設, 勢, 党, 史, 営, 府, 巻, 介, 蔵, 造, 根, 寺, 査, 将, 改, 県, 泉, 像, 細, 谷, 奥, 再, 血, 算, 象, 清, 技, 州, 領, 橋, 芸, 型, 香, 量, 久, 境, 階, 区, 波, 移, 域, 周, 接, 鉄, 頃, 材, 個, 協, 各, 帯, 歴, 編, 裏, 比, 坂, 装, 省, 税, 競, 囲, 辺, 河, 極, 防, 低, 林, 導, 森, 丸, 胸, 陸, 療, 諸, 管, 仲, 革, 担, 効, 賞, 星, 復, 片, 並, 底, 温, 軽, 録, 腰, 著, 乱, 章, 殿, 布, 角, 仏, 永, 誌, 減, 略, 準, 委, 令, 刊, 焼, 里, 圧, 額, 印, 池, 臣, 庫, 農, 板, 恋, 羽, 専, 逆, 腕, 短, 普, 岩, 竹, 児, 毛, 版, 宇, 況, 被, 岸, 超, 豊, 含, 植, 補, 暴, 課, 跡, 触, 玉, 震, 億, 肩, 劇, 刺, 述, 輪, 浅, 純, 薄, 阪, 韓, 固, 巨, 講, 般, 湯, 捨, 衣, 替, 央, 骨, 齢, 照, 層, 弱, 築, 脳, 航, 快, 翌, 旧, 筆, 換, 群, 爆, 捜, 油, 叫, 伸, 承, 雲, 練, 紹, 包, 庁, 測, 占, 混, 倍, 乳, 荒, 詰, 栄, 床, 則, 禁, 順, 枚, 厚, 皮, 輸, 濃, 簡, 孫, 丈, 黄, 届, 絡, 採, 傾, 鼻, 宝, 患, 延, 律, 希, 甘, 湾, 沈, 販, 欧, 砂, 尊, 紅, 複, 泊, 荷, 枝, 依, 幼, 斬, 勇, 昇, 寿, 菜, 季, 液, 券, 祭, 袋, 燃, 毒, 札, 狙, 脇, 卒, 副, 敬, 針, 拝, 浴, 悩, 汚, 灯, 坊, 尻, 涙, 停, 了, 汗, 郵, 幅, 童, 虫, 埋, 舟, 闇, 棒, 貨, 肌, 臓, 塩, 均, 湖, 損, 膝, 辛, 双, 軒, 績, 干, 姓, 掘, 籍, 珍, 訓, 預, 署, 漁, 緑, 畳, 咲, 貿, 踊, 封, 兆, 柱, 駐, 祝, 炭, 柔, 雇, 乾, 鋭, 氷, 隅, 冊, 糸, 募, 硬, 塗, 憎, 泥, 脂, 粉, 詞, 筒, 掃, 塔, 賢, 拾, 麦, 刷, 卵, 械, 皿, 祈, 灰, 召, 溶, 磨, 粒, 喫, 机, 貯, 匹, 綿, 贈, 凍, 瓶, 帽, 涼, 秒, 湿, 蒸, 菓, 耕, 鉱, 膚, 胃, 挟, 郊, 銅, 鈍, 貝, 缶, 枯, 滴, 符, 畜, 軟, 濯, 隻, 伺, 沸, 曇, 肯, 燥, 零, , 
            JLPT Kanji N1, 郎, 結, 氏, 衛, 第, 保, 義, 吉, 士, 藤, 井, 江, 張, 松, 応, 視, 態, 姿, 皇, 宮, 離, 基, 隊, 素, 価, 撃, 振, 証, 派, 僕, 佐, 紀, 統, 器, 異, 護, 条, 独, 源, 影, 眼, 企, 津, 案, 策, 宗, 提, 昭, 密, 司, 検, 康, 沢, 秀, 興, 率, 評, 監, 崎, 鮮, 激, 徳, 挙, 志, 敷, 系, 織, 製, 端, 遺, 房, 街, 尾, 株, 従, 敵, 展, 描, 修, 我, 載, 響, 秘, 攻, 健, 裁, 隠, 環, 援, 故, 幕, 督, 倉, 施, 嫌, 継, 障, 貴, 整, 衆, 及, 盛, 玄, 恵, 授, 弾, 養, 驚, 奈, 推, 樹, 為, 雄, 刀, 弁, 妙, 模, 抗, 級, 瞬, 称, 華, 傷, 闘, 筋, 訳, 射, 善, 黙, 柄, 刑, 節, 脱, 厳, 博, 陣, 奇, 忠, 染, 微, 標, 縁, 壁, 駆, 麻, 甲, 藩, 迫, 踏, 討, 聖, 典, 剣, 症, 納, 弥, 融, 浜, 郷, 惑, 柳, 拠, 奉, 壊, 益, 句, 属, 功, 帝, 賀, 堀, 創, 泣, 憶, 幹, 露, 矢, 握, 儀, 聴, 襲, 徴, 丁, 憲, 閣, 救, 陰, 繰, 那, 操, 騒, 己, 魔, 撮, 携, 隣, 宣, 遣, 訴, 茂, 釣, 批, 誘, 核, 哲, 豪, 締, 鹿, 就, 滅, 仰, 瀬, 致, 伏, 杉, 審, 避, 揺, 浦, 至, 裕, 盟, 執, 崩, 鬼, 酸, 拡, 銃, 維, 縄, 詩, 廃, 充, 鏡, 仮, 吐, 請, 眺, 沖, 躍, 威, 屈, 勘, 徹, 斎, 謝, 艦, 催, 舎, 仁, 衝, 脚, 虎, 潮, 穴, 怪, 仙, 輝, 緊, 唇, 忍, 狂, 奪, 診, 竜, 債, 鈴, 僧, 掲, 伯, 熊, 浪, 梅, 看, 俊, 摘, 項, 霊, 垣, 慢, 扱, 渉, 如, 縮, 詳, 旦, 慮, 雅, 砲, 謀, 懐, 愚, 舌, 駄, 奴, 豆, 又, 銭, 抑, 侍, 宙, 範, 潜, 酔, 呂, 還, 丹, 亜, 亀, 沼, 巡, 臭, 慶, 距, 釈, 侵, 僚, 悟, 隆, 裂, 尋, 旗, 羅, 揮, 票, 稲, 胞, 懸, 稿, 塚, 盤, 災, 曹, 尽, 嫁, 繁, 即, 帳, 飾, 沿, 獲, 伴, 唐, 狭, 添, 剤, 魅, 契, 邪, 挑, 免, 爵, 択, 廊, 析, 輩, 敏, 鶴, 虚, 往, 趣, 烈, 索, 匂, 摩, 菊, 滑, 沙, 裸, 孝, 綱, 邸, 邦, 揚, 卓, 騎, 墓, 姫, 孔, 耐, 須, 臨, 献, 脈, 芝, 唱, 亭, 誕, 貫, 偽, 奮, 桜, 熟, 排, 透, 棄, 削, 奏, 幻, 麗, 逮, 誠, 炎, 椅, 寛, 斉, 穂, 兼, 飼, 促, 尚, 彩, 暖, 俗, 較, 傍, 肝, 畑, 峰, 抵, 恩, 誇, 網, 渋, 魂, 牧, 控, 紛, 戒, 没, 既, 股, 脅, 征, 覆, 郡, 丘, 佳, 叔, 託, 哀, 肥, 朗, 慎, 悠, 眉, 拒, 概, 顧, 腐, 挨, 孤, 拶, 却, 賊, 荘, 匠, 悔, 獄, 滞, 遇, 淡, 購, 併, 崇, 唯, 垂, 岐, 俳, 斜, 嬢, 陥, 償, 鑑, 勧, 葬, 焦, 剛, 膨, 廷, 紫, 銘, 鎌, 菌, 稼, 譲, 随, 猛, 遂, 冒, 泰, 翼, 凄, 序, 扉, 是, 寸, 賃, 偵, 澄, 殊, 緩, 頑, 紋, 糖, 煮, 芳, 惨, 歓, 虐, 喉, 旨, 凝, 圏, 拭, 涯, 貞, 堅, 倫, 壇, 呉, 暇, 貌, 塞, 噴, 婆, 岳, 蹴, 鍵, 膳, 尺, 罰, 漏, 朱, 覧, 漂, 汁, 寂, 嘆, 禅, 浄, 酷, 刃, 漫, 霧, 暑, 棚, 袖, 壮, 旬, 彫, 需, 鎖, 潰, 縦, 粧, 慌, 穏, 枠, 謎, 誉, 逸, 駒, 惜, 措, 晶, 琴, 摂, 拍, 稽, 礎, 遭, 掌, 鍋, 弓, 克, 据, 胆, 跳, 縛, 鎮, 雷, 恨, 顕, 殖, 寧, 湧, 棋, 巧, 浸, 桃, 隔, 班, 甚, 妊, 祉, 獣, 疾, 塾, 潟, 撲, 塊, 絞, 履, 苗, 芋, 冗, 陶, 励, 陳, 猿, 葛, 傘, 啓, 劣, 撤, 殴, 盾, 衰, 滝, 慰, 蛇, 梨, 癖, 潤, 鉢, 戯, 腸, 偏, 巣, 宴, 炉, 棟, 洞, 狩, 陛, 磁, 潔, 膜, 乏, 祥, 曽, 舗, 抽, 睡, 賭, 括, 貢, 犠, 粗, 卑, 貼, 拉, 牲, 帆, 挿, 翻, 羊, 枕, 錯, 謙, 珠, 蓄, 拓, 鼓, 粋, 尉, 后, 粘, 披, 徐, 悦, 堪, 冠, 愉, 尿, 顎, 誓, 憂, 簿, 糧, 架, 芽, 軸, 苛, 蓋, 盆, 凶, 妃, 庶, 秩, 裾, 幽, 凡, 漠, 拙, 恒, 暦, 腫, 峠, 宰, 蛮, 窮, 擦, 爪, 稚, 辱, 嵐, 憤, 癒, 鬱, 疎, 雰, 彰, 肺, 傑, 拘, 頻, 緯, 妖, 豚, 藍, 矛, 鍛, 繊, 縫, 把, 楼, 捉, 漬, 紳, 飽, 宛, 閥, 旋, 坪, 崖, 叱, 鶏, 峡, 溝, 朴, 軌, 瓦, 喪, 墨, 疫, 遍, 濁, 扇, 拳, 乙, 酵, 堤, 阻, 桑, 虜, 乞, 恭, 鐘, 剰, 慈, 径, 培, 擁, 郭, 呪, 砕, 汰, 勃, 翁, 絹, 譜, 陵, 痴, 笛, 昧, 訟, 唾, 肪, 塀, 碁, 敢, 塁, 暁, 胴, 謡, 飢, 欄, 艶, 痕, 怠, 欺, 弦, 泡, 諦, 伐, 餅, 寮, 厄, 奔, 瞳, 昆, 椎, 懇, 唄, 渦, 襟, 吟, 覇, 衡, 呈, 隙, 淫, 娠, 循, 懲, 錦, 猟, 幣, 附, 箇, 醜, 箸, 戚, 喚, 紺, 某, 鋼, 褒, 赴, 媒, 妬, 遮, 窯, 侯, 釜, 茎, 蔑, 嗅, 壌, 蜜, 尼, 肢, 赦, 酬, 戴, 詠, 斗, 宜, 殻, 墳, 炊, 碑, 痩, 但, 奨, 践, 滋, 儒, 薦, 怨, 栽, 刈, 閑, 錠, 扶, 妥, 妨, 醒, 詣, 胎, 窟, 巾, 蜂, 忌, 骸, 弄, 嫉, 粛, 罵, 囚, 鉛, 搭, 諭, 璧, 阜, 喝, 享, 騰, 嗣, 勅, 篤, 勲, 埼, 伎, 曖, 詐, 餌, 岬, 暫, 爽, 肖, 詮, 諾, 柿, 芯, 綻, 訂, 汽, 薫, 隷, 俵, 遷, 枢, 肘, 麓, 憧, 帥, 漆, 酌, 頓, 賠, 渇, 慕, 婿, 妄, 慨, 匿, 渓, 侮, 髄, 穀, 薪, 轄, 洪, 牙, 咽, 迅, 該, 逐, 嘲, 墜, 臆, 餓, 挫, 錬, 桟, 溺, 賄, 盲, 鯨, 侶, 艇, 丼, 堕, 瘍, 槽, 憩, 僅, 閲, 柵, 畔, 睦, 唆, 悼, 吏, 穫, 酢, 賜, 腎, 梗, 瑠, 羨, 搬, 剖, 酎, 畿, 宵, 拐, 醸, 猶, 諮, 畏, 泌, 愁, 逝, 朽, 硫, 瞭, 擬, 叙, 弊, 累, 煩, 踪, 藻, 蚊, 栃, 且, 鋳, 蔽, 茨, 棺, 慄, 傲, 硝, 舶, 租, 倣, 謹, 抹, 虹, 捻, 娯, 臼, 喩, 萎, 蛍, 窒, 腺, 桁, 玩, 冶, 羞, 栓, 惧, 寡, 畝, 淑, 嫡, 屯, 糾, 遡, 陪, 雌, 舷, 霜, 殉, 紡, 貪, 庸, 韻, 繕, 搾, 刹, 采, 堆, 禍, 煎, 姻, 斑, 冥, 抄, 拷, 遜, 旺, 准, 勾, 廉, 礁, 壱, 麺, 升, 卸, 耗, 謁, 璃, 坑, 串, 弔, 賓, 塡, 痢, 嚇, 濫, 俸, 箋, 凸, 脊, 詔, 緻, 凹, 罷, 漸, 賦, 弧, 褐, 辣, 摯, 汎, 斥, 厘, 矯, 毀, 窃, 遵, 賂, 惰, 蚕, 氾, 諧, 倹, 款, 媛, 憾, 哺, 衷, 彙, 迭, 嘱, 恣, 墾, 逓, 劾, 酪, 沃, 塑, 痘, 憬, 朕, 虞, 丙, 斤, 捗, 弐, 訃, 謄, 繭, 璽, 頒, 楷, 剥, 籠, 錮, 頰
        
        When crafting example sentences, it's paramount that they serve as effective learning tools for students at the specified JLPT level. This goes beyond merely adhering to kanji lists; it involves ensuring the overall accessibility and naturalness of the Japanese used.

        * **MUST** construct sentences using kanji and vocabulary predominantly found within or below the grammar point's designated JLPT level. For instance, an N3 grammar point should utilize kanji and vocabulary primarily from the N5, N4, and N3 lists.
        * **MUST** prioritize creating a natural-sounding Japanese sentence. The primary goal is for the student to focus on the grammar point without being overwhelmed by unfamiliar vocabulary or complex kanji from higher levels.
        * **MUST** infer the JLPT level if it is not explicitly provided in the `jlpt` field of the grammar point. This inference should be based on common JLPT classifications for the `grammar_point` itself. For example, if "ている" is provided without a JLPT level, infer it as N5, as this is a fundamental, early-introduced grammar point.
        * **MAY** include higher-level kanji or vocabulary sparingly if absolutely necessary to demonstrate the grammar point effectively or to ensure the sentence sounds natural. This should be the exception, not the rule.
    """)
def INSPIRATION_GRAMMAR_POINTS(inpspiration_data):
    return ws("""
        ** -Inspiration grammar point- **
        This is an inspiration grammar point. Us it to help you create the grammar point, but do not copy it directly.
                                 
        BEGIN INSPIRATION_GRAMMAR_POINT
        [input_replace]
        END INSPIRATION_GRAMMAR_POINT
                             
        - *MUST NOT* use any example sentences taken literally from dojg or bunpro. 
        - **MAY** use dojg or bunpro example sentences as a reference to create your own example sentences.
        - *MUST* create your own example sentences that are appropriate for the grammar point.
    """).replace("[input_replace]", json.dumps(inpspiration_data, ensure_ascii=False, indent=4))

def PRIOR_GRAMMAR_POINT(prior_input_obj):
    return ws("""
        ** -Prior grammar point- **
        This is the prior grammar point that you will be incrementally improving.

        BEGIN PRIOR_GRAMMAR_POINT
        [prior_input_replace]
        END PRIOR_GRAMMAR_POINT

    """).replace("[prior_input_replace]", json.dumps(prior_input_obj, ensure_ascii=False, indent=4))

def ALL_GRAMMARS_SUMMARY(all_grammars_summary):
    return ws("""
        ** -Summary of all grammar points- **
        This is a list of all grammar points with truncated information to manage the size of the prompt.

        BEGIN ALL_GRAMMARS_SUMMARY
        [prior_input_replace]
        END ALL_GRAMMARS_SUMMARY

    """).replace("[prior_input_replace]", json.dumps(all_grammars_summary, ensure_ascii=False, indent=4))

def ai_pass(prior_grammar_point, all_grammars_summary, output_file, temp_dir):
    prior_input_obj = prior_grammar_point

    prompt = '\n'.join([
        PERSONA, 
        AUDIENCE,
        OUTPUT_SCHEMA,
        # KANJI_BY_LEVEL,
        # INSPIRATION_GRAMMAR_POINTS(data), 
        ALL_GRAMMARS_SUMMARY(all_grammars_summary),
        PRIOR_GRAMMAR_POINT(prior_input_obj),
        #         ws("""
        #     ** OPERATING INSTRUCTIONS **
        #     We're incrementally improving this grammar point and we're focusing on examples[].japanese
        #     right now. Follow these steps:
           
        #     for each example:
        #        add new values to the 'japanese' array.
        #        add new values to the 'competing_grammar' array.
        #        if there are no competing_grammars, you **MUST** add at least one.
           
        #        remove duplicates from 'japanese' array.
        #        remove furigana from 'japanese' array.
     
        #        for each competing_grammar:
        #           if hint reveals the grammar point to the user:
        #             change the hint to not reveal the grammar point.
           
        #     You're free to make other improvements along the way but the steps above are the main goal.
              
        #    """)
        # ws("""
        #     ** OVERRIDE OPERATING INSTRUCTIONS **
        #     ** PRIORITY INSTRUCTIONS **
        #     We're incrementally improving this grammar point and we're focusing on examples[]
        #     right now. 
        #     Output **MUST** be in JSON format following OUTPUT_SCHEMA.
           
        #     ** BEGIN PRIORITY INSTRUCTIONS ALGORITHM **
        #     Follow these steps:
        #         ------------------------------------------------------------------------------------------
        #         for each lint-error in the input:
        #             EXECUTE: Fix the lint-error.
        #         ------------------------------------------------------------------------------------------
        #     ** END PRIORITY INSTRUCTIONS ALGORITHM **
        #    """)
        ws("""
            ** OVERRIDE OPERATING INSTRUCTIONS **
            ** PRIORITY INSTRUCTIONS **
            We're incrementally improving this grammar point and we're focusing on false_friends[]
            right now. 
           
            ** BEGIN PRIORITY INSTRUCTIONS ALGORITHM **
            Follow these steps:
                ------------------------------------------------------------------------------------------
                for each false_friend in the false_friends[] array:
                    if there is no false_friend.grammar_point:
                        EXECUTE: Assign a grammar point from ALL_GRAMMARS_SUMMARY or suggest a new one.
                ------------------------------------------------------------------------------------------
            ** END PRIORITY INSTRUCTIONS ALGORITHM **
           """)
        ])

    with open(temp_dir + "/" + os.path.basename(output_file)+".prompt", 'w', encoding='utf-8') as file:
        file.write(prompt)

    grammar_point_name = prior_input_obj["grammar_point"]
    id = prior_input_obj["id"]
    sources = { }
        
    if prior_grammar_point:
        model = "gemini-2.5-flash-preview-05-20"
    else:
        model = "gemini-2.0-flash-001"
    
    for i in range(6):
      try:
        log_file = temp_dir + "/" + os.path.basename(output_file) + ".log"
        response = memoize_to_disk("ai-pass", aigen, prompt + str(i), model, GRAMMAR_SCHEMA_WITH_COMMENTS, log_file)
        response = response.removeprefix("```json").removesuffix("\n").removesuffix("```")
        response = repair_json(response)
        json_response = json.loads(response)
        json_response["id"] = id
        
        if 'rank' in json_response:
            del json_response['rank']
        if 'lesson_order' in json_response:
            del json_response['lesson_order']
        if 'bunpro' in json_response:
            del json_response['bunpro']
        if 'dojg' in json_response:
            del json_response['dojg']
        if len(sources) > 0:
            json_response['sources'] = sources

        if grammar_point_name != json_response["grammar_point"]:
            raise Exception(f"Grammar point mismatch: {data['grammar_point']} != {json_response['grammar_point']}")

        return clean_lint(json_response, output_file)
      except Exception as e:
        if i == 2:
            raise e

if __name__ == '__main__':
    # Determine workspace root: Bazel sets BUILD_WORKSPACE_DIRECTORY, otherwise use cwd
    workspace_root = os.environ.get('BUILD_WORKSPACE_DIRECTORY') or os.getcwd()
    grammar_root   = os.path.join(
        workspace_root,
        'resources', 'processed', 'ai-cleaned-merge-grammars'
    )

    temp_dir = os.path.join(workspace_root, '.temp')

    if not os.path.isdir(grammar_root):
        print(f"ERROR: “{grammar_root}” is not a directory.")
        sys.exit(1)

    # read the prior grammar summary file
    grammar_summary_file = os.path.join(grammar_root, 'summary/summary.json')
    with open(grammar_summary_file, 'r', encoding='utf-8') as f:
        grammar_summary_content = f.read()
    grammar_summary_obj = json.loads(grammar_summary_content)

    def deserialize_yaml(raw: str):
        return yaml.load(raw, Loader=yaml.CSafeLoader)

    def preprocess(parsed_obj, file_path):
        result = clean_lint(parsed_obj, file_path)
        # if len(result.get('lint-errors', [])) == 0:
        #     return None # Skip this one
        return result

    def logic(parsed_obj, file_path):
        return ai_pass(parsed_obj, grammar_summary_obj, file_path, temp_dir)

    def serialize_json(obj):
        return json.dumps(obj, ensure_ascii=False, indent=4)

    mr = MapReduce(
        input_dir            = grammar_root,
        output_dir           = grammar_root,
        deserialize_func     = deserialize_yaml,
        preprocess_func      = preprocess,
        map_func_name        = "ai generating",
        map_func             = logic,
        serialize_func       = serialize_json,
        temp_dir             = temp_dir,
        max_threads          = 15,
    )

    asyncio.run(mr.run())

