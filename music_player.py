
from tkinter import *
import pygame
from tkinter import filedialog
import time
from mutagen.mp3 import MP3
from tkinter import ttk
import os
window=Tk()
window.resizable(False,False)
window.title("Music Player 🎶")
pygame.mixer.init()
songs=[]
#song adding function
def add_song():
    global song_dir
    global current_song
    global song_list
    global my_menu
    song_dir=filedialog.askdirectory(title="Select Folder")
    for song in os.listdir(song_dir):
        name,ext=os.path.splitext(song)
        if ext==".mp3":
          song_list.insert(END,song)
    path=os.path.basename(song_dir)
    window.title(path)
    my_menu.entryconfig(1,state="disabled")
    my_menu.entryconfig(2,state="normal")
    back_btn.config(state="normal")
    pause_btn.config(state="normal")
    play_btn.config(state="normal")
    next_btn.config(state="normal")
    current_music=song_list.select_set(0)
    current_music=song_list.activate(0)
def play_time():
    try:

     current_time=pygame.mixer.music.get_pos()//1000
     converted_current_time=time.strftime("%M:%S",time.gmtime(current_time))
     current_song=song_list.curselection()
     song=song_list.get(current_song)
     current =os.path.join(song_dir,staus_label.cget("text"))
     song_Mut=MP3(current)
     song_length=song_Mut.info.length
     converted_song_length=time.strftime("%M:%S",time.gmtime(song_length))
     status_bar["text"]=f"{converted_current_time} of {converted_song_length} "
     if int(current_time)+1>=int(song_length):

          
          if current_song[0]+1>=song_list.size():
              song_list.delete(ACTIVE)
              pygame.mixer.music.stop()
              song_list.select_set(0)
              song_list.activate(0)
              play_btn.config(state="normal")
              status_bar.config(text="")
              staus_bar.config(text="")
              return
          else:
              
              return nextt(),playy()
     print(current_time,int(song_length))
     status_bar.after(1000,play_time)
    except Exception as e:
        print(e)
#delete a song function
def delete_song():
          stop()
          play_btn.config(state="normal")
          song_list.delete(ACTIVE)
          pygame.mixer.music.stop()
          song_list.select_set(0)
          song_list.activate(0)
          staus_label.config(text="")
          if song_list.size()==0:
                    my_menu.entryconfig(1,state="normal")
                    my_menu.entryconfig(2,state="disabled")
                    back_btn.config(state="disabled")
                    pause_btn.config(state="disabled")
                    play_btn.config(state="disabled")
                    next_btn.config(state="disabled")  


     
#delete all songs function
def delete_all_songs():
     stop()
     staus_label.config(text="")
     song_list.delete(0,END)
     pygame.mixer_music.fadeout(1)
     my_menu.entryconfig(1,state="normal")
     my_menu.entryconfig(2,state="disabled")
     back_btn.config(state="disabled")
     pause_btn.config(state="disabled")
     play_btn.config(state="disabled")
     next_btn.config(state="disabled")    

#Play time

#stop function
global stopped
stopped=False
def stop():
    status_bar.config(text="")
 
    pygame.mixer.music.stop()
    song_list.selection_clear(ACTIVE)
    status_bar.config(text="")
    global stopped
    stopped=True
                      
#buttons functions
def backk():
     global song_dir
     try:
         global song_list
         song=song_list.get(ACTIVE)

         play_btn.config(state="normal")
         next_song=song_list.curselection()

         if next_song[0]-1<0:
              pass
         else:
            next_one=next_song[0]-1
            song=song_list.get(next_one)
            song_list.selection_clear(0,END)
            song_list.activate(next_one)
            song_list.selection_set(next_one,last=None)
 
     except Exception as e:
          print(e)
def nextt():
     global song_dir
     try:
         global song_list
         song=song_list.get(ACTIVE)

         play_btn.config(state="normal")
         next_song=song_list.curselection()

         if next_song[0]+1>=song_list.size():
              pass
         else:
            next_one=next_song[0]+1
            song=song_list.get(next_one)
            song_list.selection_clear(0,END)
            song_list.activate(next_one)
            song_list.selection_set(next_one,last=None)
            
     except Exception as e:
          print(e)
global paused
paused =False

def playy():
        song=song_list.get(ACTIVE)
        play_btn.config(state="disabled")
        global song_dir
        try: 
                    current_music=song_list.get(ACTIVE)
                    staus_label.config(text=current_music)
                    pygame.mixer_music.load(os.path.join(song_dir,current_music))
                    pygame.mixer_music.play()
                    staus_label.config(text=song)
                    return play_time()
##                    song_position=int(song_length)  
        except EXCEPTION as e:
                    print(e)
        
def pausee():
     global paused
     if paused == False:
         pygame.mixer_music.pause()
         paused =True
     else:
          pygame.mixer_music.unpause()
          paused=False
vol_bool=False
def vol():
     global vol_bool
     if vol_bool == False:
         window.geometry("550x600")
         vol_bool =True
     else:
          window.geometry("500x600")
          vol_bool=False

def volume(x):
    pygame.mixer.music.set_volume((vol_slider.get()/100))

res=False
#button images
bac=PhotoImage(file="assets/previous.png")
nex=PhotoImage(file="assets/next.png")
pla=PhotoImage(file="assets/play4.png")
pau=PhotoImage(file="assets/pause2.png")

#listbox and volume frame
display_frame=Frame(window)
display_frame.pack()
#playlist bg=PISTACHIO
window.geometry("500x600")
song_list=Listbox(display_frame,bg="#33ccff",fg="black",width=61,height=20,selectbackground="black",font="Calibri 12",selectforeground="white",activestyle=None)
song_list.grid(padx=5,row=0,column=0)

wong_list=[]
#music_volume slider

vol_slider=ttk.Scale(display_frame,from_=100,to=0,value=50,orient=VERTICAL,length=400,command=volume)
vol_slider.grid(padx=10,row=0,column=1,sticky=E)
#=====
songg=""
staus_label=Label(window)
staus_label.pack()
#-----
#status
status_bar=Label(window,text="00:00",bd=1,relief=GROOVE,anchor=E)
status_bar.pack(fill=X,ipady=2,side=BOTTOM)

#Control panel with buttons

control_panel=Frame(window)
control_panel.pack()
global back_btn
global next_btn
global play_btn
global pause_btn
back_btn=Button(control_panel,image=bac,command=backk,borderwidth=0)
back_btn.grid(row=0,column=0,padx=10)
next_btn=Button(control_panel,image=nex,command=nextt,borderwidth=0)
next_btn.grid(row=0,column=3,padx=5)
play_btn=Button(control_panel,image=pla,command=playy,borderwidth=0)
play_btn.grid(row=0,column=2,padx=10)
pause_btn=Button(control_panel,image=pau,command=pausee,borderwidth=0)
pause_btn.grid(row=0,column=1,padx=10)

##loop_btn=Button(control_panel,text="Loop",command=loop)
##loop_btn.grid(row=0,column=4,padx=10)
###############THEMES###################################
'''
def default_theme():
     window.configure(bg="lightblue")
     back_btn.config(bg="lightblue",activebackground="lightblue")
     pause_btn.config(bg="lightblue",activebackground="lightblue")
     play_btn.config(bg="lightblue",activebackground="lightblue")
     next_btn.config(bg="lightblue",activebackground="lightblue")
     display_frame.config(bg="lightblue")
     control_panel.config(bg="lightblue")
     bac=PhotoImage(file="assets/back_blue.png")
     nex=PhotoImage(file="assets/next_blue.png")
     pla=PhotoImage(file="assets/play_blue.png")
     pau=PhotoImage(file="assets/pause_blue.png")
     back_btn.config(image=bac)
     pause_btn.config(image=pau)
     play_btn.config(image=pla)
     next_btn.config(image=nex)
     staus_label.config(bg="lightblue")

'''
#==================================================
back_btn.config(state="disabled")
pause_btn.config(state="disabled")
play_btn.config(state="disabled")
next_btn.config(state="disabled")

#menu
global add_song_menu
my_menu=Menu(window)
window.config(menu=my_menu)
#creating menu buttons 
add_song_menu=Menu(my_menu,tearoff=False)
delete_song_menu=Menu(my_menu,tearoff=False)
volume=Menu(my_menu,tearoff=False)
add_themes=Menu(my_menu,tearoff=False)
#menu cascading
my_menu.add_cascade(label="File",menu=add_song_menu)
my_menu.add_cascade(label="Remove songs",menu=delete_song_menu)
my_menu.add_cascade(label="Volume",command=vol)
my_menu.add_cascade(label="Theme",menu=add_themes)
#adding submenu_label
add_song_menu.add_command(label="Select the song",command=add_song)
delete_song_menu.add_command(label="Delete a song",command=delete_song)
delete_song_menu.add_command(label="Delete all the songs",command=delete_all_songs)

my_menu.entryconfig(2,state="disabled")

window.mainloop()

