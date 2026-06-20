import streamlit as st
from google import genai
from google.genai import types
import json
import time

st.title("🧶 Holding Steady")

st.caption(
    "'I believe we can do it, because we are thinking about it now.'",
)

with st.sidebar:
    st.header("About")

    st.write(
        "A supportive chatbot designed for thoughtful and empathetic conversations."
    )

    if st.button("Clear Chat"):
        st.session_state.chat_state = None
        st.rerun()

    st.space("xxlarge")

    st.header("Emotional Support Buddy")
    st.video("Moufu_vid.mp4", autoplay=True, muted=True)
    



############# CONFIGURE CHAT

GEMINI_API_KEY = st.secrets["API_KEY"]
client = genai.Client(api_key=GEMINI_API_KEY)

######## FIX VARIABLES

INTENT_LABELS = [
    "venting",
    "advice",
    "grounding",
    "agency",
    "recognition",
    "reassurance",
    "safety",
    "general_support"
]

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
- Ask at most one gentle follow-up question.
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
- Ask one gentle follow-up question to understand what they need.
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

    if output['intent_label'] not in INTENT_LABELS:
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
    # format messages 
    conversation_text = format_conversation(messages)

    # prompt sharing existing messages and asking next reply
    prompt = f""" 
    Here is the conversation so far:
    {conversation_text}

    Write the assistant's next reply.
    Do not repeat the user's message.
    Do not repeat previous assistant messages.    
    """ 

    # query to AI to get response
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
    # classify the user's first message    
    classification = classify_first_message(first_user_message)
    intent_label = classification['intent_label']

    # choose the system prompt for that intent  
    system_prompt = get_system_prompt_for_intent(intent_label)

    # start the conversation history
    messages = [
        {'role': 'user', 'content': first_user_message}
    ]

    # generate the assistant reply
    assistant_reply = generate_chat_reply(messages, system_prompt)
    
    # save the assistant reply    
    messages.append({'role': 'assistant', 'content': assistant_reply})

    # store everything we need for the chat session
    chat_state = {
        'classification': classification,
        'intent_label': intent_label,
        'system_prompt': system_prompt,
        'messages': messages
    }

    # return the ff: classification results, intent label, system prompt, messages
    return chat_state


def continue_chat(chat_state, new_user_message):
    # add the new user message    
    chat_state['messages'].append({
        'role': 'user',
        'content': new_user_message
    })

    # generate assistant reply using conversation history    
    assistant_reply = generate_chat_reply(chat_state['messages'], chat_state['system_prompt'])
    
    # save the assistant reply    
    chat_state['messages'].append({'role': 'assistant', 'content': assistant_reply})

    # save assistant reply
    return assistant_reply





######## CHAT INPUT

user_input = st.chat_input(
    "Type your message here..."
)


####### CHAT LOGIC

if "chat_state" not in st.session_state:
    st.session_state.chat_state = None


with st.chat_message("assistant"):
    st.markdown("Hello! How may I help you today?")

if st.session_state.chat_state:
    messages = st.session_state.chat_state['messages']
    for message in messages:
        with st.chat_message(message['role']):
            st.markdown(message['content'])


if user_input:

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
        with st.spinner("Thinking..."):
            st.markdown(bot_reply)
