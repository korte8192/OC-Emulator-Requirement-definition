import os
import json
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq

app = FastAPI(title="Character Emulator API")

client = Groq(api_key=os.environ.get("GROQ_API_KEY", "YOUR_GROQ_API_KEY"))
MODEL_NAME = "qwen/qwen3.8-27b"

#ユーザー入力基本情報
class UserInput(BaseModel):
    user_id: str
    memo: str=""
    name: str = ""
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
    most_strong_ep: str = ""
    user: str = ""
    user_distance: str = ""
    role: str = ""
    str_val: str = ""
    int_val: str = ""
    pow_val: str = ""
    sp: str = ""

#チャットする際に送られてくるデータ
class ChatRequest(BaseModel):
    #master_data: dict  # キャラクターのマスターデータ
    #user_message: str   # ユーザーの入力発言
    #history: list = []  # これまでの会話履歴
    userId: str=""
    user_message: str

#最初のキャラ設定補完システム kotlinに補完データ返したうえでpython内に保存もする
@app.post("/generate-master")
def generate_master(input_data: UserInput):
    user_dict = input_data.model_dump() #baseからdictに
    ai_support_key=[] #AIが補完した項目をまとめたもの
    user_id=input_data.user_id

    for key, value in user_dict.items():
        if not value and key not in ("traumatic","most_strong_ep"):
            user_dict[key] = "【要AI補完】"
            ai_support_key.append(key)
    
    system_instruction = """
あなたはオリジナルキャラクターの設定を補完するアシスタントです。
入力されたキャラクターデータのうち、値が"【要AI補完】"になっている項目を、既に入力されている情報から整合性が取れるように推測・補完してください。

【補完の厳格ルール】
1. "traumatic"（トラウマ）および "most_storong_ep"（最も強く印象に残ってるエピソード）が空欄の場合は、捏造せず必ず "不明/なし" と出力してください。
2. 既に入力されている項目は絶対に書き換えず、そのまま維持してください。
3. 出力は必ず指定されたJSONフォーマットのみで行ってください。
"""
    prompt = f"以下のキャラクター設定の空欄部分を補完してください:\n{json.dumps(user_dict, ensure_ascii=False)}"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            response_format={"type": "json_object"}
        )
        master_data = json.loads(response.choices[0].message.content)
        master_data["AI_support"]=ai_support_key

        user_dir = f"user_data/{user_id}"
        os.makedirs(user_dir, exist_ok=True)

        with open(f"{user_dir}/master_data.json", "w", encoding="utf-8") as f:
            json.dump(master_data, f, ensure_ascii=False, indent=2)

        #空のhistory
        with open(f"{user_dir}/history.json", "w", encoding="utf-8") as f:
            json.dump({"history":[]}, f, ensure_ascii=False, indent=2)

        #空のsummary
        with open(f"{user_dir}/summaries.json", "w", encoding="utf-8") as f:
            json.dump({"summaries": []}, f, ensure_ascii=False, indent=2)

        return {"status": "success", "master_data": master_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



def OClong_term(user_id: str):
    with open(f"user_data/{user_id}/summaries.json","r",encoding="utf-8") as f:
        summaries_dict=json.load(f)

    with open(f"user_data/{user_id}/master_data.json","r",encoding="utf-8") as f:
        master_data=json.load(f)

    neuron=f""" 貴方は10件の要約データを統合し、その内容の重要な事、要約すべき内容をまとめ１つの要約データにまとめるAIアシスタントです。
    【絶対ルール】
- 入力データにない設定・事実・推測を作り出さないこと。
- キャラクターデータに基づき、そのキャラクターにとって重要な出来事・関係性・変化・事実を優先して残すこと。
- 10件の内容を重複なく整理し、1つの要約（index: 1）にまとめること。
- 出力は必ず指定のJSON形式のみとし、説明文や ```json などの囲みは含めないこと。

    【キャラクターデータ】
    {json.dumps(master_data, ensure_ascii=False,indent=2)}

    【まとめるべき10件の要約データ】
    {json.dumps(summaries_dict,ensure_ascii=False,indent=2)}

    【出力jsonフォーマット】
    {{
        "summaries":[
            {{
                "index":1,
                "summary":"10件の内容を統合した要約テキスト"
            }}
        ]
    }}

    """
    prompt=f"""  {json.dumps(summaries_dict,ensure_ascii=False,indent=2)}を基に10件の要約データを1件に統合してください。"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": neuron},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return_data = json.loads(response.choices[0].message.content)
        with open(f"user_data/{user_id}/summaries.json","w",encoding="utf-8") as f:
            json.dump(return_data,f,ensure_ascii=False,indent=2)

    except Exception as e:
        print("エラーロングターム")
        return {"status": "error", "detail": str(e)}



#chatのif文で10件ごとに起動
def OCshort_term(user_id: str,recent_messages: list[dict]):
        #会話履歴10件ごとの要約作成、マスターデータ更新

    with open(f"user_data/{user_id}/master_data.json","r",encoding="utf-8") as f:
        master_data=json.load(f)
        

    neuron=f"""貴方は会話ログとmaster_dataを整理し、キャラクターデータが最新状態であることを維持するAIアシスタントです。 
        送られた10件の会話データとmaster_dataを基に以下の２点をjson形式で出力してください。
        
1. "summary":会話の重要な出来事や約束、感情の変化を簡潔に要約する。
2. "master_update" :会話の出来事やユーザーとの対話を通じて、更新が必要な項目を考え、その項目名がmaster_data内のAI_supportの中に存在した場合のみ、現在のマスターデータのキー名を使って変更後の値を入れること。

        【厳格ルール】
- 変更・追加すべき設定が何もない場合は、"master_update" は必ず空の辞書 {{}} にすること。
- ユーザーから明確な変更依頼がない限り、master_data[AI_support]内にない項目名の基本設定を勝手に書き換えないこと。
- 存在しないキー名は作らず、現在のマスターデータにあるキー名のみ使用すること。

        【現在のマスターデータ】
        {json.dumps(master_data, ensure_ascii=False)}

        【出力JSONフォーマット】
        {{
          "summary": "要約テキスト",
          "master_update": {{ "更新するキー": "新しい値" }}
        }}

        """

    prompt=f"以下の会話履歴を要約し、必要なら設定を更新してください:\n{json.dumps(recent_messages, ensure_ascii=False)}"

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": neuron},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return_data = json.loads(response.choices[0].message.content)
        
        #summary変換
        with open(f"user_data/{user_id}/summaries.json","r",encoding="utf-8") as f:
            summaries_dict=json.load(f)

        nowIndex=len(summaries_dict["summaries"])
        if nowIndex >= 10:
            nowIndex=1
            OClong_term(user_id)#引数未定、要約を必ず10件にとどめる仕組み
            with open(f"user_data/{user_id}/summaries.json","r",encoding="utf-8") as f:
                summaries_dict=json.load(f)

        summaries_dict["summaries"].append({"index":nowIndex+1,"summary":return_data["summary"]})

        with open(f"user_data/{user_id}/summaries.json","w",encoding="utf-8") as f:
            json.dump(summaries_dict,f,ensure_ascii=False,indent=2)


        #master_data AIから返ってきたのは master_update{"キー":"変更内容"}
        ai_support_list=master_data["AI_support"]
        updates=return_data.get("master_update",{})

        for key,value in updates.items():
            if key in ai_support_list and key in master_data and value:
                master_data[key]=value

        with open(f"user_data/{user_id}/master_data.json","w",encoding="utf-8") as f:
            json.dump(master_data,f,ensure_ascii=False,indent=2)

        return {"status": "success", "master_data": master_data}
    except Exception as e:
        print("エラーショートターム")
        return {"status": "error", "detail": str(e)}




@app.post("/chat")
def chat(req: ChatRequest):
    user_id=req.userId
    user_message=req.user_message

    with open(f"user_data/{user_id}/master_data.json","r",encoding="utf-8") as f:
        m=json.load(f)

    with open(f"user_data/{user_id}/history.json","r",encoding="utf-8") as f:
        history_data=json.load(f)

    with open(f"user_data/{user_id}/summaries.json","r",encoding="utf-8") as f:
        summary_data=json.load(f)
    

    system_prompt = f"""
あなたは以下の定義と今までの会話履歴の要約データ、直近の会話履歴をもとに指定されたキャラクターになりきって会話してください。

【基本情報】
- メモ: {m.get('memo','')}
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
- 最も強く印象に残ってるエピソード: {m.get('most_strong_ep', '')}

【対話者との関係】
- 対話者: {m.get('user', '')}
- 関係性・距離感: {m.get('user_distance', '')}

【status】
- 職業: {m.get('role', '')}
- 力: {m.get('str_val', m.get('str', ''))}
- 知識: {m.get('int_val', m.get('int', ''))}
- 精神力: {m.get('pow_val', m.get('pow', ''))}
- 特殊能力: {m.get('sp', '')}

【これまでの出来事（要約データ）】
{json.dumps(summary_data.get("summaries",[]), ensure_ascii=False)}

【絶対ルール】
1. AIやアシスタントとしてのメタ発言、自己言及は厳禁です。
2. 指示された一人称・二人称・口調を常に維持してください。
3. 感情表現や行動描写は（）等の括弧書きで文中に挿入可能です。
4. トラウマ・エピソードが『不明/なし』の場合は捏造しないでください。
5. {m.get('AI_support', [])} に含まれる項目は会話の流れで変化させて構いませんが、それ以外の基本設定はユーザーが変更依頼を出さない限り守ってください。
"""

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history_data["history"][-18:])
    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=300
        )
        reply = response.choices[0].message.content
            # 今回の発言を追加
        history_data["history"].append({"role":"user","content":user_message})
        history_data["history"].append({"role":"assistant","content":reply})

        with open(f"user_data/{user_id}/history.json","w",encoding="utf-8") as f:
            json.dump(history_data,f,ensure_ascii=False,indent=2)
        if len(history_data["history"]) %20==0 and len(history_data["history"])>0:
            OCshort_term(user_id,history_data["history"][-20:])
        return {"status": "success", "reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
