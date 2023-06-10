import openai


def get_gpt_response(messages):
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    gpt_response = completion.choices[0].message.content
    return gpt_response

def create_image_with_prompt(prompt):
    response = openai.Image.create(
        prompt = prompt,
        n=1,
        size="512x512",
    )

    

    return response.data[0].url