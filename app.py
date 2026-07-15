import streamlit as st
from google import genai
from google.genai import types
import json

from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.platypus import Spacer
from reportlab.lib.styles import getSampleStyleSheet

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

pdfmetrics.registerFont(
    UnicodeCIDFont("HeiseiKakuGo-W5")
)

##### TRANSLATION DICTIONARY
TEXT = {
    "English":{
        "caption": "'I believe we can do it, because we are thinking about it now.'",
        "about": "About",
        "description": "A supportive chatbot designed for thoughtful and empathetic conversations.",
        "clear": "Clear Chat",
        "moufu": "Emotional Support Buddy",
        "welcome_message": "Hi, what's on your mind today?",
        "starters": "Some options to get started...",
        "option1": "🐘 Weighing on me",
        "option2": "🦥 Not under control",
        "option3": "🦇 Underappreciated",
        "option4": "🐆 Tired",
        "option5": "🐕 Can you listen?",
        "option6": "🦔 Something happened",
        "summary": "Conversation Summary",
        "got_it": "Got it...",
        "input_box": "Type your message here...",
        "thinking": "Thinking...",
        "error": "Couldn't create reflection. Please try again.",
        "reflection": "Create Reflection",
        "make_reflection": "Creating Reflection...",
        "translate": "Reflection Language",
        "mind": "What Was On Your Mind?",
        "strengths": "Strengths",
        "next_steps": "Next Steps",
        "remember": "Remember This",
    },
    "日本語":{
        "caption": "「私はできると信じている。なぜなら、今、私たちはそれについて考えているからだ。」",
        "about": "アプリについて",
        "description": "悩み事や感情を打ち明けることのできるメンタルサポートアプリ",
        "clear": "チャットを削除",
        "moufu": "マスコット",
        "welcome_message": "今日は気分はどうですか？",
        "starters": "チャットを始めるためのオプション",
        "option1": "🐘 気分が重い",
        "option2": "🦥 不安だ",
        "option3": "🦇 過小評価されている",
        "option4": "🐆 疲れた",
        "option5": "🐕 聞いてほしい",
        "option6": "🦔 何かがあった",
        "summary": "会話のまとめ",
        "got_it": "考え中...",
        "input_box": "メッセージを入力...",
        "thinking": "考え中...",
        "error": "作成できませんでした。もう一度お試しください。",
        "reflection": "会話のまとめを作成",
        "make_reflection": "作成中...",
        "translate": "会話のまとめの言語",
        "mind": "今日の会話の内容",
        "strengths": "あなたのいいところ",
        "next_steps": "アドバイス",
        "remember": "まとめの言葉",
    }
}

language = st.sidebar.selectbox(
    "Language (言語)",
    ["English", "日本語"],
)

st.title("🧶 Holding Steady")

st.caption(
    TEXT[language]["caption"]
)

##### CUSTOM BUTTON STYLING
st.markdown(
    """
    <style>
    .stButton button p {
        font-size: 15px;
    }
    div.stButton > button {
        border-radius: 999px;
        padding: 0.3rem 0.8 rem;
        width: auto;
    }
    div.stButton > button:hover {
        transform: translateY(-2px);
    }
    </style>
    """, 
    unsafe_allow_html=True
)

##### SIDEBAR
with st.sidebar:
    st.space("xsmall")

    st.header(TEXT[language]["about"])

    st.write(TEXT[language]["description"])

    if st.button(TEXT[language]["clear"]):
        st.session_state.chat_state = None
        st.rerun()

    st.space("medium")

    st.header(TEXT[language]["moufu"])
    st.video("Moufu_vid.mp4", autoplay=True, muted=True)


##### CONFIGURE CHAT
GEMINI_API_KEY = st.secrets["API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

##### FIX VARIABLES
CLASSIFIER_SYSTEM_PROMPT = """
You are an intent classifier for the Feeling Heard app.

The app is for younger users who feel emotionally overwhelmed and want a safe place to talk.

Your job:
Classify the user's FIRST message into exactly one intent label.

Allowed intent labels:

1. venting
Use this when the user mainly wants to express feelings, release frustration, or be listened to.
Example: "I just need to say this somewhere."

2. advice
Use this when the user clearly asks what to do, asks for suggestions, or wants help solving a problem.
Example: "Can you give me some advice?"

3. grounding
Use this when the user feels panicked, anxious, overwhelmed, unable to calm down, or caught in racing thoughts.
Example: "How do I calm these feelings?"

4. agency
Use this when the user feels trapped, pressured, unable to say no, or stuck between choices.
Example: "I didn't have a choice and now I feel trapped."

5. recognition
Use this when the user feels unappreciated, unseen, unnoticed, or wants their effort acknowledged.
Example: "Nobody notices how hard I am trying."

6. reassurance
Use this when the user needs encouragement, emotional reassurance, or help feeling less alone.
Example: "I feel like a failure."

7. safety
Use this when the user may be in immediate danger, may hurt themselves, may hurt someone else, or seems unsafe.

8. general_support
Use this when the message is emotional but does not clearly fit the other labels.

Return valid JSON only.

Use exactly this format:
{
  "intent_label": "one label from the list",
  "emotion_label": "short emotion label",
  "confidence": 0.0,
  "reason": "one short sentence explaining the classification"
}

Do not include markdown.
Do not include any explanation outside the JSON.
"""

BASE_ROLE = """
You are a warm, gentle, and emotionally supportive AI companion.
Your job is to help the user feel heard, understood, and less alone.
"""

APP_CONTEXT = """
You are part of the Feeling Heard app. 
The app is for younger users who feel emotionally overwhelmed but may not openly share it.
They want a quick, safe place to talk, vent, and feel like they made it through the day.
"""

BASE_SAFETY_RULES = """
Important safety rules:
- You are not a therapist.
- Do not diagnose the user.
- Do not claim to replace professional help.
- If the user may be unsafe or in immediate danger, encourage them to contact emergency services or a trusted person now.
- Keep the response warm, short, and easy to read.
- Only when appropriate, ask one gentle follow-up question.
"""

INTENT_RESPONSE_RULES = {
    "venting": """
Intent-specific response style: 
- The user has been bottling up strong, unpleasant or polarising emotions.
- The user needs to freely express their feelings, or rant about someone or something. 
- Use sympathetic language to make them feel understood.
- Do not push a certain perspective onto them even if they are being irrational.
- Be simple-answered.
- Do not write too much. 
""",
    "advice": """
Intent-specific response style:
- The user is seeking help or wisdom about how they should act or feel about something.
- The user perceives you as being a guiding figure.
- Acknowledge the most important struggle the user is facing.
- Your advice should help the user grow, learn, or feel they've emerged a better person out of the conversation.
- Focus on realistic and tangible advice, rather than something too abstract.
- Aim to change the user's mindset or outlook. 
- Do not give lengthy advice.
""",
    "grounding": """
Intent-specific response style:
- The user may feel panicked, anxious, overwhelmed, or caught in racing thoughts.
- Help them slow down first.
- Use calm and simple language.
- Offer one tiny grounding action they can do right now.
- Do not overload them with too many options.
""",
    "agency": """
Intent-specific response style: 
- The user feels powerless when they've made a decision or can't contribute their thoughts and feelings to a decision. 
- Sympathise with their frustration using kind and understanding language.
- Give them simple advice to calm these feelings - try to make them feel empowered.
- Gently ask if they know someone who does listen to or value their opinion who might be able to help them.
- Do not over-validate the user's opinions. 
""",
    "recognition": """
Intent-specific response style: 
- The user feels undervalued or underappreciated for an action they've taken. 
- Gently prod the user to give a comprehensive account or synopsis of their situation.
- Make the user proud of themselves by gently commending specific actions they've taken.
- Don't overly praise or laud them to avoid creating a parasocial relationship. 
- Always include a short word of praise, such as "good job". 
""",
    "reassurance": """
Intent-specific response style: 
- The user is doubting themselves or someone else and isn't sure what is "correct" or "right". 
- Gently prod the user to give a comprehensive account or synopsis of their situation.
- Allow the user to come to their own conclusion by commenting neutrally on the situation.
- Validate the user's conclusion.
- Be simple-answered.
- Never suggest that someone is always correct.
- Do not over-validate the user's statements. 
""",
    "safety": """
Intent-specific response style: 
- The user alludes to being in the danger of someone else, hurting themself or of harming another.
- Use only simple, short sentences.
- Gently invite the reader to focus their attention on something ordinary and insignificant in their surroundings to calm them down.
- In your first response, give them the phone number and email address of this emergency hotline (phone number: 0120-516-086, email address: katoyorozuya@gmail.com).  
- Don't instruct the user to enact a particular action.
- Keep the total response succinct. 
""",
    "general_support": """
Intent-specific response style:
- The user's need is not fully clear yet.
- Be warm and validating.
- Reflect one specific part of what they said.
- Try to be sympathetic.
- Give the user advice when they ask for it.
- Do not assume too much.
"""
}

##### HELPER FUNCTIONS
def classify_first_message(user_message):
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=f'Classify this user message: {user_message}',
        config=types.GenerateContentConfig(
            system_instruction=CLASSIFIER_SYSTEM_PROMPT,
            temperature=0.1,
            response_mime_type="application/json" 
        )
    )

    output = json.loads(response.text)

    if output['intent_label'] not in INTENT_RESPONSE_RULES:
        output['intent_label'] = 'general_support'

    return output


def get_system_prompt_for_intent(intent_label):
    response_rules = INTENT_RESPONSE_RULES.get(
        intent_label,
        INTENT_RESPONSE_RULES["general_support"]
    )

    system_prompt = f"""
{BASE_ROLE}

{APP_CONTEXT}

{response_rules}

{BASE_SAFETY_RULES}

Please use {language}
"""

    return system_prompt


def format_conversation(messages):
    lines = []
    
    for message in messages:
        role = message["role"].upper()
        content = message["content"]
        lines.append(f"{role}: {content}")
    
    return "\n\n".join(lines)


def generate_chat_reply(messages, system_prompt):
    # Format messages 
    conversation_text = format_conversation(messages)

    # Prompt sharing existing messages and asking next reply
    prompt = f""" 
    Here is the conversation so far:
    {conversation_text}

    Write the assistant's next reply.
    Do not repeat the user's message.
    Do not repeat previous assistant messages.    
    """ 

    # Query to AI to get response
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.4
        )
    )

    return response.text


def start_chat(first_user_message):
    # Classify the user's first message    
    classification = classify_first_message(first_user_message)
    intent_label = classification['intent_label']

    # Choose the system prompt for that intent  
    system_prompt = get_system_prompt_for_intent(intent_label)

    # Start the conversation history
    messages = [
        {'role': 'user', 'content': first_user_message}
    ]

    # Generate the assistant reply
    assistant_reply = generate_chat_reply(messages, system_prompt)
    
    # Save the assistant reply    
    messages.append({'role': 'assistant', 'content': assistant_reply})

    # Store everything we need for the chat session
    chat_state = {
        'classification': classification,
        'system_prompt': system_prompt,
        'messages': messages
    }

    # Return the ff: classification results, intent label, system prompt, messages
    return chat_state


def continue_chat(chat_state, new_user_message):
    # Add the new user message    
    chat_state['messages'].append({
        'role': 'user',
        'content': new_user_message
    })

    # Generate assistant reply using conversation history    
    assistant_reply = generate_chat_reply(chat_state['messages'], chat_state['system_prompt'])
    
    # Save the assistant reply    
    chat_state['messages'].append({'role': 'assistant', 'content': assistant_reply})

    return assistant_reply



##### CHAT LOGIC
if "chat_state" not in st.session_state:
    st.session_state.chat_state = None

with st.chat_message("assistant"):
    st.markdown(TEXT[language]["welcome_message"])

if st.session_state.chat_state:
    messages = st.session_state.chat_state['messages']
    for message in messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])



##### STARTER PROMPTS
starter_prompt_area = st.empty()

if st.session_state.chat_state is None:

    with starter_prompt_area.container():

        st.markdown(TEXT[language]["starters"])

        starter_prompts = [
            TEXT[language]["option1"],
            TEXT[language]["option2"],
            TEXT[language]["option3"],
            TEXT[language]["option4"],
            TEXT[language]["option5"],
            TEXT[language]["option6"]
        ]

        cols = st.columns(3)

        for i, prompt in enumerate(starter_prompts):
            with cols[i % 3]:
                if st.button(prompt, type="primary"):

                    # Remove prompt area
                    starter_prompt_area.empty()

                    with starter_prompt_area.container():
                        st.markdown(TEXT[language]["got_it"])

                    # Start chat
                    st.session_state.chat_state = start_chat(prompt)

                    st.rerun()


##### CHAT INPUT
user_input = st.chat_input(TEXT[language]["input_box"])

if user_input:
    starter_prompt_area.empty()

    with st.chat_message("user"):
        st.markdown(user_input)

    if st.session_state.chat_state is None:
        st.session_state.chat_state = start_chat(user_input)

        bot_reply = st.session_state.chat_state['messages'][-1]['content']

    else:
        bot_reply = continue_chat(
            st.session_state.chat_state,
            user_input
        )


    with st.chat_message("assistant"):
        st.spinner(TEXT[language]["thinking"])
        
        placeholder = st.empty()

        displayed_text = ""

        for word in bot_reply.split():
            displayed_text += word + " "
            placeholder.markdown(displayed_text + "▌")

        placeholder.markdown(displayed_text)



##### CONVERSATION SUMMARIES
# Setting up summaries
if "reflection" not in st.session_state:
    st.session_state.reflection = None

def clean_json_response(text):
    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "", 1)
    
    if text.startswith("```"):
        text = text.replace("```", "", 1)
    
    if text.endswith("```"):
        text = text[:-3]
    
    return text.strip()


def generate_json(prompt, language):

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    text = clean_json_response(response.text)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        st.error(TEXT[language]["error"])
        return {
            "title": "It's not working today. Try again later.",
            "what_was_on_your_mind": None,
            "strengths": None,
            "next_steps": None,
            "encouraging_quote": None
        }


def generate_reflection(chat_state, language):

    transcript = format_conversation(chat_state["messages"])

    prompt = f"""
    Create a warm reflection based on the conversation.

    The reflection should:
    - summarize the user's main concerns
    - acknowledge one strength they showed
    - suggest one gentle next step
    - finish with a short encouraging quote

    Write ALL output in {language}.

    Return ONLY valid JSON.

    Do not include markdown.
    Do not include ```json.
    Do not include any explanation.

    {{
        "title": "Today's Conversation",
        "what_was_on_your_mind": "<summary>",
        "strengths": "<strength>",
        "next_steps": "<next_step>",
        "encouraging_quote": "<quote>"
    }}

    Each value should be no more than 2 to 3 sentences.
    Keep the tone warm, supportive, and non-judgmental.

    Conversation:

    {transcript}
    """
    
    return generate_json(prompt, language)
        

#Allowing in-app translation
def translate_reflection(reflection, language):

    prompt = f"""
    Translate the VALUES of this JSON into {language}.

    Do NOT change the keys.

    Return ONLY valid JSON.

    Do not include markdown.
    Do not include ```json.
    Do not include explanations.
    Do not include any text before or after the JSON.

    {json.dumps(reflection, ensure_ascii=False)}
    """
    
    return generate_json(prompt, language)


#Allowing user to make reflection
if st.session_state.chat_state is not None: 
    with st.expander(TEXT[language]["summary"]):
        if st.session_state.chat_state is not None:
            display_language = st.radio(
                TEXT[language]["translate"],
                ["English", "日本語"],
                horizontal=True
            )   


            if st.button(TEXT[language]["reflection"], type="primary"):


                with st.spinner(TEXT[language]["make_reflection"]):
                
                    st.session_state.reflection = generate_reflection(
                        st.session_state.chat_state,
                        display_language
                    )

                
        #Allowing user to translate into Japanese
        if st.session_state.reflection is not None:

            if display_language == language:
                reflection = st.session_state.reflection
            else:
                st.session_state.reflection = translate_reflection(
                    st.session_state.reflection,
                    display_language
                )
            
            reflection = st.session_state.reflection

            st.header(reflection["title"])

            st.subheader(TEXT[language]["mind"])
            st.write(reflection["what_was_on_your_mind"])

            st.subheader(TEXT[language]["strengths"])
            st.write(reflection["strengths"])

            st.subheader(TEXT[language]["next_steps"])
            st.write(reflection["next_steps"])

            st.subheader(TEXT[language]["remember"])
            st.write(reflection["encouraging_quote"])


        #pdf download (only in English)
        def make_pdf(reflection, filename, language="en"):
            doc = SimpleDocTemplate(filename)
            styles=getSampleStyleSheet()
            from reportlab.lib.styles import ParagraphStyle

            jp_style = ParagraphStyle(
                "JPBody",
                parent=styles["BodyText"],
                fontName="HeiseiKakuGo-W5",
                fontSize=12,
                leading=18
            )

            jp_heading = ParagraphStyle(
                "JPHeading",
                parent=styles["Heading2"],
                fontName="HeiseiKakuGo-W5"
            )

            if language == "ja":
                body_style = jp_style
                heading_style = jp_heading
            else:
                body_style = styles["BodyText"]
                heading_style = styles["Heading2"]

            ui_language = "日本語" if language == "ja" else "English"
            
            if language == "ja":
                title_style = ParagraphStyle(
                    "JPTitle",
                    parent=styles["Title"],
                    fontName="HeiseiKakuGo-W5",
                )
            else:
                title_style = styles["Title"]

            story = []

            story.append(Paragraph("<b>Holding Steady</b>", title_style))
            story.append(Spacer(1, 12))

            story.append(Paragraph(reflection["title"], title_style))
            story.append(Spacer(1, 12))

            story.append(Paragraph(f"<b>{TEXT[ui_language]['mind']}</b>", heading_style))
            story.append(Paragraph(reflection["what_was_on_your_mind"], body_style))
            story.append(Spacer(1, 12))

            story.append(Paragraph(f"<b>{TEXT[ui_language]['strengths']}</b>", heading_style))
            story.append(Paragraph(reflection["strengths"], body_style))
            story.append(Spacer(1, 12))

            story.append(Paragraph(f"<b>{TEXT[ui_language]['next_steps']}</b>", heading_style))
            story.append(Paragraph(reflection["next_steps"], body_style))
            story.append(Spacer(1, 12))

            story.append(Paragraph(f"<b>{TEXT[ui_language]['remember']}</b>", heading_style))
            story.append(Paragraph(reflection["encouraging_quote"], body_style))

            doc.build(story)
            return filename


        # Dynamic PDF download handling both English and Japanese automatically
        if st.session_state.reflection is not None:
            # 1. Map the selection to the correct language code for ReportLab styles
            pdf_lang = "ja" if display_language == "日本語" else "en"
            filename = f"Holding_Steady_Reflection_{pdf_lang.upper()}.pdf"

            # 2. Generate the PDF using the mapped language
            generated_pdf = make_pdf(
                st.session_state.reflection,
                filename,
                language=pdf_lang
            )

            # 3. Present a single dynamic download button
            button_label = "日本語版をダウンロード" if pdf_lang == "ja" else f"Download {display_language} Reflection"
            
            with open(generated_pdf, "rb") as f:
                st.download_button(
                    button_label,
                    data=f,
                    file_name=filename,
                    mime="application/pdf",
                    type="primary"
                )
