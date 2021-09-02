from flask import Flask,request,send_file,flash,redirect,url_for,Response
from flask_cors import CORS
from threading import Thread
import subprocess
import asyncio
from shlex import quote, join
import base64
import os
import io
from werkzeug.utils import secure_filename
from mutagen.id3 import ID3,TRCK,TIT2,TALB,TPE1,APIC,TDRC,COMM,TPOS,USLT,error
from mutagen.mp3 import MP3
import random
import glob

UPLOAD_FOLDER = 'image/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask('')
CORS(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = "bananaman"


global working

@app.route('/')
def home():
    return "Hello. I am alive!"

@app.route('/delete')
def delete():
  fileList = glob.glob('*.mp3')
  # Iterate over the list of filepaths & remove each file.
  for filePath in fileList:
      try:
          os.remove(filePath)
      except OSError:
          print("Error while deleting file")

  return 'Deleted: ' + str(fileList)

@app.route('/log')
def log():
 with open('log.txt', 'r') as file:
    data = file.read()
    fdata = "data: "+data+"\n\n"
    return Response(fdata, mimetype="text/event-stream")
    


@app.route('/check')
def check():
  try:
    working
  except NameError:
      return 'I\'m good!'
  else:    
    if working == True:
      return"I'm busy..."
    elif working == False:
      return 'I\'m good!'  

@app.before_request
def before_request_func():
    working = True

@app.after_request
def after_request_func(response):
  working = False
  return response


@app.teardown_request
def teardown_request_func(error=None):
  working = False



@app.route('/download',methods=['GET', 'POST'])
async def json_example():
    working = True
    
    url = request.args.get('url')
    author = request.args.get('author')
    title = request.args.get('title')
    album = request.args.get('album')
    
    
    print('Downloading...')
    coms = ['youtube-dl', '-f','251','-g','--get-filename','-o','%(title)s','--force-ipv4',url]
    print(join(coms))
    process = subprocess.Popen(coms, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
    stdout,stderr = process.communicate()
    link = stdout.splitlines()[-2]
    print(link+"\n"+link+"\n"+link)
    title_safe = stdout.splitlines()[-1]+"_"+str(random.randint(1000,9999))
    print(title_safe+"\n"+title_safe+"\n"+title_safe)
    if os.path.exists(title_safe+".mp3"):
        file_path = title_safe+".mp3"
        return_data = io.BytesIO()
        with open(file_path, 'rb') as fo:
            return_data.write(fo.read())
        # (after writing, cursor will be at last byte, so move it to start)
        return_data.seek(0)
        os.remove(file_path)
        response = send_file(return_data,mimetype='image/png', attachment_filename=title_safe+".mp3")
        
        return response


    else:  
      coms = ['ffmpeg', '-i',  link, '-codec:a', 'libmp3lame', '-q:a', '0', title_safe+".mp3"]
      process = subprocess.Popen(coms, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
      for line in process.stdout:
        print(line)
        with open('log.txt', 'w') as file:
          f = open("log.txt", "w")
          f.write(line)
          f.close()
      #return 'Downloading...'+ ' '+url
      with open('log.txt', 'w') as file:
        f = open("log.txt", "w")
        f.write('DONE!')
        f.close()
      audio = MP3(title_safe+".mp3", ID3=ID3)
      try:
          audio.add_tags()
      except error:
          pass
      audio.tags.add(TIT2(encoding=3, text=title))
      audio.tags.add(TALB(encoding=3, text=author+" - "+title))
      audio.tags.add(TPE1(encoding=3, text=author))
      

      
      #response.headers.add('Access-Control-Allow-Origin', '*')
      file = request.files['file']
      img_name = 'img_'+str(random.randint(1000,9999))
      file.save(os.path.join(app.config['UPLOAD_FOLDER'], img_name+'.png'))

      

      file = request.files['file']
      print(request.files)
      # if user does not select file, browser also
      # submit an empty part without filename

  #   if file and allowed_file(file.filename):
    #    filename = secure_filename(file.filename)
  #     file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
      audio.tags.add(APIC(mime='image/png',type=3,desc=u'Cover',data=open('image/'+img_name+'.png','rb').read()))   
      audio.save() 
      os.remove('image/'+img_name+'.png')
      file_path = title_safe+".mp3"
      return_data = io.BytesIO()
      with open(file_path, 'rb') as fo:
          return_data.write(fo.read())
      # (after writing, cursor will be at last byte, so move it to start)
      return_data.seek(0)
      os.remove(file_path)
      response = send_file(return_data,mimetype='image/png', attachment_filename=title_safe+".mp3")
      
      return response

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/a', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part

        file = request.files['file']
        print(request.files)
        # if user does not select file, browser also
        # submit an empty part without filename

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            return 'Done!'

def run():
  app.run(host='0.0.0.0',port=8080)

def run_gunicorn():
  coms = ['gunicorn', '--workers','4','--bind','0.0.0.0:5000','wsgi:app']
  print(join(coms))
  process = subprocess.Popen(coms, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)
  for line in process.stdout:
        print(line)

def keep_alive():
    t = Thread(target=run)
    t.start()

  # gunicorn --workers 4 --bind 0.0.0.0:5000 wsgi:app