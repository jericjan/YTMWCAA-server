from flask import Flask,request,send_file,flash,redirect,url_for,Response,session
from flask_session import Session
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
import string
import glob
import datetime
import uuid

UPLOAD_FOLDER = 'image/'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}

app = Flask('')
#app.secret_key = "bananaman"
CORS(app, supports_credentials=True)
sess = Session()

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SECRET_KEY'] = "bananaman"
app.config["SESSION_TYPE"] = "filesystem"
sess.init_app(app)

app.config.update(SESSION_COOKIE_SAMESITE="None", SESSION_COOKIE_SECURE=True)


def random_string():
  source = string.ascii_letters + string.digits
  result_str = ''.join((random.choice(source) for i in range(8)))
  return result_str

global working

@app.route('/')
def home():
    return "Hello. I am alive!"

@app.route('/delete')
def delete():
  fileList = glob.glob('*.mp3') + glob.glob('*.txt')
  # Iterate over the list of filepaths & remove each file.
  for filePath in fileList:
      try:
          os.remove(filePath)
      except OSError:
          print("Error while deleting file")

  return 'Deleted: ' + str(fileList)

 
    

@app.route('/go',methods=['GET', 'POST'])
async def go():
    
  session['UserID'] = random_string()
  session.modified = True

  print(session['UserID'])
  return "'GO! succeeded"

@app.route('/get',methods=['GET', 'POST'])
async def get():
  try:
   return session['UserID']
  except Exception:
      return 'Couldn\'nt find UserID :('

@app.route('/get_uuid',methods=['GET', 'POST'])
async def get_uuid():
  return str(uuid.uuid4())

@app.route('/reset',methods=['GET', 'POST'])
def reset():
  try:
      session.pop('UserID',None)
  except Exception:
      pass
  return 'reset succeeded'

@app.route('/log',methods=['GET', 'POST'])
async def log():
 uuid = request.args.get('pogid') #uuid gets blocked by ublock lmao 
 try: 
  with open('log_'+str(uuid)+'.txt', 'r') as file:
      #if file.startswith('size=    '):
        data0 = file.read().split('time=')[1].split(' ')[0]
        print(data0)
     # else:
     #   data0 = '0'  
     #   print(data0)
    #    data00 = data0.split('time=')[1].split(' ')[0]
    #    print(data00)
    #  else:
    #    pass  

  with open('duration_'+str(uuid)+'.txt', 'r') as file:
      data1 = file.read()    
   #   print(data1)
    #  print('logged: '+data)
     # fdata = "data: "+data+"\n\n"
 # print(data00+" / "+data1)   
  try:
    ct = datetime.datetime.strptime(data0,"%H:%M:%S.%f")
    tt = datetime.datetime.strptime(data1.strip(),"%H:%M:%S.%f")
    delta_ct = datetime.timedelta(hours=ct.hour, minutes=ct.minute, seconds=ct.second,microseconds=ct.microsecond)
    delta_tt = datetime.timedelta(hours=tt.hour, minutes=tt.minute, seconds=tt.second,microseconds=tt.microsecond)
    ff = tt-ct
    perc=round((delta_ct / delta_tt)*100,1)

    percent_time = " ("+str(perc)+"%)"
    print(percent_time)
  except Exception as e:
    print(e)
  print(data0+" / "+data1)  
  return Response("data: "+data0+" / "+data1+percent_time+"\n\n", mimetype="text/event-stream")
 except Exception as e:
      data = "Beep boop..."
      return  Response("data: "+data+"\n\n", mimetype="text/event-stream")




@app.route('/download',methods=['GET', 'POST'])
async def json_example():
    
    uuid = request.args.get('uuid')
    print(uuid)
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
    title_safe = stdout.splitlines()[-1]+"_"+str(uuid)
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
       # print(line)
        if line.startswith('  Duration: '):
          with open('duration_'+str(uuid)+'.txt', 'w') as file:
            f = open('duration_'+str(uuid)+'.txt', "w")
            f.write(line.split('Duration:')[1].split(',')[0])
            f.close()  
        else:  
          with open('log_'+str(uuid)+'.txt', 'w') as file:
            f = open('log_'+str(uuid)+'.txt', "w")
            f.write(line)
            f.close()
      #return 'Downloading...'+ ' '+url
  #    with open('log_'+session['UserID']+'.txt', 'w') as file:
  ##      f = open('log_'+session['UserID']+'.txt', "w")
   #     f.write('Bleep bloop...')
  #      f.close()
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
      img_name = 'img_'+str(uuid)
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
      os.remove('log_'+str(uuid)+'.txt')
      response = send_file(return_data,mimetype='image/png', attachment_filename=title_safe+".mp3")
      os.remove('duration_'+str(uuid)+'.txt')
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