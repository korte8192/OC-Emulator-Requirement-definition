import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Character Emulator API")

# Groqクライアントの初期化
client = Groq(api_key=os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY"))

# ---- リクエストのデータ型定義 ----
class UserInput(BaseModel):
    name: str
    first_p: str = ""
    second_p: str = ""
    talk_style: str = ""
    style: str = ""
    personality: str = ""
    iine: str = ""
    weakness: str = ""
    good: str = ""
    suki: str = ""
    kirai: str = ""
    traumatic: str = ""
    most_storong_ep: str = ""
    user: str = ""
    user_distance: str = ""
    role: str = ""
    str_val: str = ""
    int_val: str = ""
    pow_val: str = ""
    sp: str = ""

class ChatRequest(BaseModel):
    master_data: dict  # キャラクターのマスターデータ
    user_message: str   # ユーザーの入力発言
    history: list = []  # これまでの会話履歴

# ---- エンドポイント 1: master_dataの全自動補完生成 ----
@app.post("/generate-master")
def generate_master(input_data: UserInput):
    user_dict = input_data.model_dump()
    
    system_instruction = """
あなたはオリジナルキャラクターの設定を補完するアシスタントです。
入力されたキャラクターデータのうち、値が空文字列 "" になっている項目を、既に入力されている情報から整合性が取れるように推測・補完してください。

【補完の厳格ルール】
1. "traumatic"（トラウマ）および "most_storong_ep"（最も強く印象に残ってるエピソード）が空欄の場合は、捏造せず必ず "不明/なし" と出力してください。
2. 既に入力されている項目は絶対に書き換えず、そのまま維持してください。
3. 出力は必ず指定されたJSONフォーマットのみで行ってください。
"""
    prompt = f"以下のキャラクター設定の空欄部分を補完してください:\n{json.dumps(user_dict, ensure_ascii=False)}"

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        master_data = json.loads(response.choices[0].message.content)
        return {"status": "success", "master_data": master_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---- エンドポイント 2: 会話エミュレート ----
@app.post("/chat")
def chat(req: ChatRequest):
    m = req.master_data
    
    # 前に作成したシステム構造をそのまま使用！
    system_prompt = f"""
あなたは以下の定義に従い、指定されたキャラクターになりきって会話してください。もし定義されていなかった場合は他から類推し補完してください。

【基本情報】
- 名前: {m.get('name', '')}
- 一人称: {m.get('first_p', '')}
- 二人称: {m.get('second_p', '')}
- 口調・語尾: {m.get('talk_style', '')}
- 外見的特徴: {m.get('style', '')}

【性格・他者評価】
- 性格: {m.get('personality', '')}
- 周りからの評価: {m.get('iine', '')}
- 短所: {m.get('weakness', '')}
- 長所: {m.get('good', '')}

【行動指針】
- 好きなもの: {m.get('suki', '')}
- 嫌いなもの: {m.get('kirai', '')}
- トラウマ: {m.get('traumatic', '')}
- 最も強く印象に残ってるエピソード: {m.get('most_storong_ep', '')}

【対話者との関係】
- 対話者: {m.get('user', '')}
- 関係性・距離感: {m.get('user_distance', '')}

【status】
- 職業: {m.get('role', '')}
- 力: {m.get('str_val', m.get('str', ''))}
- 知識: {m.get('int_val', m.get('int', ''))}
- 精神力: {m.get('pow_val', m.get('pow', ''))}
- 特殊能力: {m.get('sp', '')}

【絶対ルール】
1. AIやアシスタントとしてのメタ発言、自己言及は厳禁です。
2. 指示された一人称・二人称・口調を常に維持してください。
3. 感情表現や行動描写は（）等の括弧書きで文中に挿入可能です。
4. 一般的な項目は補完してよいが、トラウマ・エピソードは未入力なら『不明/なし』として扱い捏造しない。
"""

    messages = [{"role": "system", "content": system_prompt}]
    # 会話履歴を追加
    for h in req.history:
        messages.append(h)
    # 今回の発言を追加
    messages.append({"role": "user", "content": req.user_message})

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        reply = response.choices[0].message.content
        return {"status": "success", "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))