import openai


class openai_utils:
    def __init__(self, model="gpt-4-1106-preview", image_size="512x512") -> None:
        self.model = model
        self.image_size = image_size

    def get_gpt_response(self, messages):
        completion = openai.ChatCompletion.create(model=self.model, messages=messages)

        gpt_response = completion.choices[0].message.content
        return gpt_response

    def create_image_with_prompt(self, prompt):
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size=self.image_size,
        )
        return response.data[0].url

    def get_model(self):
        return self.model
