# Welcome to the ParticleSims Repo!

**Table of contents:**
---
> 1. [About ParticleSims](#about)  
> 2. [Getting Started](#gettingStarted)
> 3. [Things To Do](#notes)
---


<a name="about"></a>
## About ParticleSims
ParticleSims is an interactive particle simulation built using Py5, a Python frontend to the Java processing library.
With the simulation you can experiment with simple rules to create different types of particles in a 2D pixel grid.
A big shout out goes to Sanjay for coming up with the idea and creating the initial project!   
 
![Demo](media/demo.gif)

<a name="gettingStarted"></a>
## Getting Started

As mentioned in the about section, py5 leverages Java Processing library and as such requires that Java be installed on the system and configured correctly. Before getting started make sure that Java is already installed on your system and that the `JAVA_HOME` environment variable is correctly set.

Once Java is installed clone this repository and install the python requirements  
First clone the repo and install the required python packages:
```bash
git clone https://github.com/samrg123/pcepProgrammingClub.git
cd ./pcepProgrammingClub/particleSims
pip install -r ./requirements.txt
```

Then execute the program according to your needs:
```bash
usage: main.py [-h] [--width WIDTH] [--height HEIGHT] [--size SIZE]

An interactive particle simulation App

options:
  -h, --help       show this help message and exit
  --width WIDTH    The width of the viewport in grid units
  --height HEIGHT  The height of the viewport in grid units
  --size SIZE      The size of each grid in pixels
```
> Note: if executed without any arguments the program will use a 50x50 size viewport with a grid size of 10 pixels 


<a name="notes"></a>
## Things to Do
- By default the program includes three particles: *Sand*, *RainbowSand*, *Fire*, and *MyParticle*. You can select between the types of particles by pressing the keys 1-4 on your keyboard. Once a particle is selected you can hold down the left mouse button to continually spawn particles under the pointer, tap the middle mouse button to spawn a single particle, or hold the right mouse button to continually remove particles. 
- In `main.py` there is an `MyParticle` class with TODO's where you can customize *MyParticle*. Mess around with it and see what you can create! Some ideas include, but are not limited to:
    - A Bomb particle that explodes neighboring particles 
    - A Plant particle that grows into a tree over time if planted on Sand
    - A Cloud particle that floats to the sky and rains
- If you get stuck feel to checkout how the other particles were implemented in `src/particles.py` or ask for help / suggestions!

