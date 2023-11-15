from flask import Flask
from flask import render_template
from flask import Response, request, jsonify
app = Flask(__name__)

#for gpt
import os
import openai

import secretsk
openai.api_key = secretsk.SECRET_KEY



#for dalle
import json
from base64 import b64decode
from pathlib import Path



#Thid is the basic data representation
songs_data = {
  "songs":"",
  "themes":"",
  "suggestions":[],
  "generations":[]
}

dreams_data = {
    "dream": "",
    "mood": "",
    "themes": [],
    "interpretations": [],
    "average_rating": 0
}

# This is what the representation looks like when there are keywords and images generated
# sample_headline_data_2 = {
#    "generations": [
#       {
#          "prompt": "Santos’s Lies Were Known to Some Well-Connected Republicans",
#          "url": "static/generated_images/Santo-1673801357/Santo-1673801357-0.png"
#       },
#       {
#          "prompt": "Santos’s Lies Were Known to Some Well-Connected Republicans",
#          "url": "static/generated_images/Santo-1673801375/Santo-1673801375-0.png"
#       }
#    ],
#    "headline": "Santos’s Lies Were Known to Some Well-Connected Republicans",
#    "keywords": [
#       "Santos",
#       "Lying",
#       "Republican",
#       "2022",
#       "Suspicion",
#       "Campaign",
#       "Upperechelons",
#       "Republicans",
#       "Turned a Blind Eye",
#       "Connection"
#    ],
#    "summary": "George Santos inspired no shortage of suspicion during his 2022 campaign, including in the upper echelons of his own party, yet many Republicans looked the other way."
# }



sample_headline_data_1 = {

    "headline": "See a new comet before it vanishes for 400 years",
    "summary": "CAPE CANAVERAL, Fla. (AP) — A newly discovered comet is swinging through our cosmic neighborhood for the first time in more than 400 years. Stargazers across the Northern Hemisphere should catch a glimpse as soon as possible — either this week or early next — because it will be another 400 years before the wandering ice ball returns. The comet, which is kilometer-sized (1/2-mile), will sweep safely past Earth on Sept. 12, passing within 78 million miles (125 million kilometers).",
    "keywords": [],
    "newsong": [],
}



#### INIT with example data
# headline_data = sample_headline_data_1





@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    global dreams_data
    data = request.get_json()   

    dreams_data["interpretations"][-1]["rating"] = data

    i = 0
    for interpretation in dreams_data["interpretations"]:
        avg


    #send back the WHOLE array of data, so the client can redisplay it
    return jsonify(dreams_data)

@app.route('/submit_headline', methods=['GET', 'POST'])
def submit_headline():
    global dreams_data
    data = request.get_json()

    dreams_data["dream"] = data["dream"]
    dreams_data["mood"] = data["mood"]

    #send back the WHOLE array of data, so the client can redisplay it
    return jsonify(dreams_data)


@app.route('/get_images', methods=['GET', 'POST'])
def get_images():
    global headline_data
    data = request.get_json()   
    # print(data)
    prompt = data["prompt"]
    new_images = generate_images(prompt)

    for i in new_images:
        headline_data["generations"].append(i) 

    #just send new images
    return jsonify(new_images)



def generate_images(prompt):
    response = openai.Image.create(
        prompt=prompt,
        n=1,
        size="256x256",
        response_format="b64_json",
    )

    #create json file for image
    DATA_DIR = Path.cwd() / "responses"
    DATA_DIR.mkdir(exist_ok=True)
    JSON_FILE = DATA_DIR / f"{prompt[:5]}-{response['created']}.json"
    with open(JSON_FILE, mode="w", encoding="utf-8") as file:
        json.dump(response, file)  


    #convert json image data file to png
    IMAGE_DIR = Path.cwd() / "static/generated_images" / JSON_FILE.stem

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)

    with open(JSON_FILE, mode="r", encoding="utf-8") as file:
        response = json.load(file)

    for index, image_dict in enumerate(response["data"]):
        image_data = b64decode(image_dict["b64_json"])
        image_file = IMAGE_DIR / f"{JSON_FILE.stem}-{index}.png"
        with open(image_file, mode="wb") as png:
            png.write(image_data)    

    full_path_to_image = image_file.as_posix()
    url_for_flask = full_path_to_image[full_path_to_image.find('static'):]

    print("url_for_flask")
    print(url_for_flask)

    images = [
        {
            "prompt": prompt,
            "url": url_for_flask, #image_file.as_posix(),
        }
    ]
    print(url_for_flask)
    return images


@app.route('/get_keywords', methods=['GET', 'POST'])
def get_keywords():
    global dreams_data

    dream = dreams_data["dream"]

    suggestions = get_song_suggestions(dream)
    dreams_data["themes"] = suggestions
    print(dreams_data["themes"])

    #send back the WHOLE array of data, so the client can redisplay it
    return jsonify(dreams_data)

@app.route('/write_song', methods=['GET', 'POST'])
def write_song():
    global dreams_data

    dream = dreams_data["dream"]
    mood = dreams_data["mood"]
    theme = request.get_json()

    interpretation = interpret_dream(dream, mood, theme)
    dreams_data["interpretations"].append({theme: interpretation})

    #send back the WHOLE array of data, so the client can redisplay it
    print(dreams_data)
    return jsonify(dreams_data)

def interpret_dream(dream, mood, theme):
    prompt = "Given a dream and some information on the person's mood, analyze the symbol: " + theme + " through the framework of Jungian dream analysis. Dream: " + dream + "." + "Mood: " + mood +"."
    #prompt = "tell me a joke"
    print("prompt printing here:")
    print(prompt)

    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=1000)["choices"][0]["text"]
    #print("response printing here:")
    #print(response)
    return response.strip()

def parse_keywords_from_gpt_response(keyword_response):
    keyword_list = keyword_response.splitlines()
    new_keyword_list = []
    for i, item in enumerate(keyword_list):
        item = item.strip()
        if item != "":
            item = item[item.index(".") + 1:]
            item = item.strip()
            new_keyword_list.append(item)
    return new_keyword_list

def write_new_song(songs, themes):
    prompt = "write me a new song with guitar chord progression that is similar to these songs: " + songs + ". Include these themes: " + themes + "."
    #prompt = "tell me a joke"
    print("prompt printing here:")
    print(prompt)

    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=1000)["choices"][0]["text"]
    #print("response printing here:")
    #print(response)
    return response

def get_song_suggestions(dream):
    #prompt = "Give me 5 song suggestions based on these similar songs and themes. songs:  " + songs + ". themes: " + themes
    prompt = "Create a list of the most important symbols in this dream: " + dream + "Use the following format: symbol, symbol, symbol."
    print("prompt printing here:")
    print(prompt)

    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=256)["choices"][0]["text"]
    print("response printing here:")
    print(response)
    ### PARSE THEM HERE!
    keyword_list = response.strip().split(',')

    return keyword_list
'''
def get_keywords_for_headline(headline, summary):
    prompt = "Give me 10 keywords that represent this news headline and summary and format it like this: \n 1. keyword1 \n 2. keyword2 \n 3. keyword three. News headline: "+headline+". News summary: "+summary+"."
    #print(prompt)
    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, max_tokens=256)["choices"][0]["text"]
    
    ### PARSE THEM HERE!
    keyword_list = []
    try:
        keyword_list = parse_keywords_from_gpt_response(response)
    except:        
        print("ERROR: gpt keyword response won't parse")
        print(response)

    return keyword_list

'''
@app.route('/')
def home():
    # you can pass in an existing article or a blank one.
    return render_template('home.html', data=songs_data)


if __name__ == '__main__':
    # app.run(debug = True, port = 4000)    
    app.run(host='0.0.0.0',port=8000)




