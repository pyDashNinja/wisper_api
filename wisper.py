import whisper
import soundfile as sf
from flask import Flask, request, jsonify, send_file, send_from_directory
import random
import os
import pandas as pd
import io
from datetime import datetime
import time


def generate_subtitles(mp3_path, output_path):

    # Get text from speech for subtitles from audio file
    result = model.transcribe(mp3_path)

    # Create Subtitle dataframe and save it as SRT file
    dict1 = {'start': [], 'end': [], 'text': []}
    for i in result['segments']:
        dict1['start'].append(int(i['start']))
        dict1['end'].append(int(i['end']))
        dict1['text'].append(i['text'])
    df = pd.DataFrame.from_dict(dict1)

    with open(output_path, 'w') as f:
        for index, row in df.iterrows():
            start_time = row['start']
            end_time = row['end']
            subtitle_text = row['text']
            f.write(f"{index+1}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{subtitle_text}\n")
            f.write("\n")


def inference(audio):
    result = model.transcribe(audio)
    print(result["text"])
    return result["text"]


app = Flask(__name__)


# before request
@app.before_request
def before_request():
    # check if model global variable has been initialized
    if 'model' not in globals():
        global model
        model = whisper.load_model("small")
    else:
        print("Model already loaded")


@app.route('/transcribe', methods=['POST'])
def transcribe():
    try:
        if request.method == 'POST':
            if 'file' not in request.files:
                return jsonify({'error': 'no file'})
            file = request.files['file']
            if file.filename == '':
                return jsonify({'error': 'no file'})
            if file:

                # generate current time with date and time with microseconds
                randomnumber = datetime.now().strftime("%Y%m%d%H%M%S%f")
                print(randomnumber)
                randomnumber = str(randomnumber) + \
                    str(random.randint(0, 100000000))
                print(randomnumber)

                # now we want to save the file
                file.save(f"./Temp/{randomnumber}tmp.wav")
                generate_subtitles(
                    f"./Temp/{randomnumber}tmp.wav", f"./Temp/{randomnumber}tmp.srt")
                os.remove(f"./Temp/{randomnumber}tmp.wav")

                # srt_path = f"./Temp/{randomnumber}tmp.srt"
                return send_file(f"./Temp/{randomnumber}tmp.srt", mimetype='application/x-subrip', as_attachment=True)
    except Exception as e:
        print(e)
        return jsonify({'error': str(e)})

    finally:
        try:
            # get all files which were created 10 minutes ago with end with .srt in Temp folder
            files = [f for f in os.listdir(
                './Temp') if os.path.isfile(os.path.join('./Temp', f))]
            for f in files:
                if f.endswith(".srt"):
                    if os.path.getmtime(os.path.join('./Temp', f)) < (time.time() - 600):
                        os.remove(os.path.join('./Temp', f))
        except Exception as e:
            pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3737, debug=True)
