import pygame
from pygame import mixer #music
import os
import random
import csv
import button

pygame.init()
mixer.init()

#game window
SCREEN_WIDTH=800 
SCREEN_HEIGHT= int(SCREEN_WIDTH*0.8)
screen = pygame.display.set_mode((SCREEN_WIDTH,SCREEN_HEIGHT))
pygame.display.set_caption('Combattant')

#set framerate
clock=pygame.time.Clock()
FPS=60

#define game variables
GRAVITY=0.75
SCROLL_THRESH=200 #SCREEN WILL MOVE WHEN THE PLAYER GETS WITHIN 200 PIXELS OF THE EDGE
ROWS=16
COLS=150
TILE_SIZE=SCREEN_HEIGHT//ROWS
TILE_TYPES=21
MAX_LEVELS=3
screen_scroll=0 #main
bg_scroll=0
level=1
start_game=False
start_intro=False


#define player action variables
moving_left=False
moving_right=False
shoot=False
grenade=False
grenade_thrown=False

#load music
pygame.mixer.music.load('audio/Scamsong.mp3')
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1, 0.0, 5000)# no of loops, delay, fade(ms)
jump_fx=pygame.mixer.Sound('audio/jump.wav')
jump_fx.set_volume(0.5)
grenade_fx=pygame.mixer.Sound('audio/grenade.wav')
grenade_fx.set_volume(0.5)
shot_fx=pygame.mixer.Sound('audio/shot.wav')
shot_fx.set_volume(0.5)





#load images
#button images
start_img=pygame.image.load('img/start_btn.png').convert_alpha() #to convert surfaces to the same pixel format as used by the screen so you won't lose performance because of conversions when you're blitting them to the screen.
exit_img=pygame.image.load('img/exit_btn.png').convert_alpha()
restart_img=pygame.image.load('img/restart_btn.png').convert_alpha()
#bg images
pine1_img=pygame.image.load('img/Background/pine1.png').convert_alpha()
pine2_img=pygame.image.load('img/Background/pine2.png').convert_alpha()
mountain_img=pygame.image.load('img/Background/mountain.png').convert_alpha()
sky_img=pygame.image.load('img/Background/nightsky2.jpg').convert_alpha()
#store tiles in list
img_list=[]
for x in range(TILE_TYPES):
	img=pygame.image.load(f'img/Tile/{x}.png').convert_alpha()
	img=pygame.transform.scale(img, (TILE_SIZE, TILE_SIZE))
	img_list.append(img)
#bullet
bullet_img=pygame.image.load('img/icons/bullet.png').convert_alpha()
#grenade image
grenade_img=pygame.image.load('img/icons/grenade.png').convert_alpha()
#pick up boxes
health_box_img=pygame.image.load('img/icons/health_box.png').convert_alpha()
ammo_box_img=pygame.image.load('img/icons/ammo_box.png').convert_alpha()
grenade_box_img=pygame.image.load('img/icons/grenade_box.png').convert_alpha()
item_boxes={
	'Health'	:	health_box_img,
	'Ammo'		: 	ammo_box_img,
	'Grenade'	: 	grenade_box_img

}

#define colors
BG=(144, 201, 120)
RED=(255,0,0)
WHITE=(255,255,255)
GREEN=(0,255,0)
BLACK=(0,0,0)
PINK=(235, 65,54)
#define font
font=pygame.font.SysFont('Futura',30)


def draw_text(text, font, text_col, x, y): #text_col=text color
	img=font.render(text, True, text_col)
	screen.blit(img, (x,y))

def draw_bg():
	screen.fill(BG)
	width=sky_img.get_width()
	for x in range(5):
		screen.blit(sky_img, ((x*width) - bg_scroll * 0.5,0))
		screen.blit(mountain_img, ((x*width) - bg_scroll * 0.6, SCREEN_HEIGHT- mountain_img.get_height()-300))
		screen.blit(pine1_img, ((x*width) - bg_scroll * 0.7, SCREEN_HEIGHT- pine1_img.get_height()-150))
		screen.blit(pine2_img, ((x*width)- bg_scroll * 0.8, SCREEN_HEIGHT- pine2_img.get_height()))

#function to restart level
def reset_level():
	enemy_group.empty()
	bullet_group.empty()
	grenade_group.empty()
	explosion_group.empty()
	item_box_group.empty()
	decoration_group.empty()
	water_group.empty()
	exit_group.empty()

	#create empty tile list
	data=[]
	for row in range(ROWS):
		r=[-1]*COLS
		data.append(r)
	return data

class Combattant(pygame.sprite.Sprite):
	#x and y to allocate the player
	def __init__(self, char_type, x, y, scale, speed, ammo, grenades):
		pygame.sprite.Sprite.__init__(self)
		self.alive=True
		self.char_type=char_type
		self.vel_y=0
		self.speed=speed
		self.ammo=ammo
		self.start_ammo=ammo
		self.shoot_cooldown=0
		self.grenades=grenades
		self.health=100
		self.max_health=self.health
		self.direction=1
		self.jump=False
		self.in_air=True
		self.flip=False
		self.animation_list=[]
		self.frame_index=0
		self.action=0
		self.update_time=pygame.time.get_ticks()
		#create ai specific variables
		self.move_counter=0
		self.idling=False
		self.idling_counter=0
		self.vision=pygame.Rect(0,0,150,20)

		#load all images of players
		animation_types=['Idle', 'Run','Jump', 'Death']
		for animation in animation_types:
			#reset temporary list of images
			temp_list=[]
			#count number of files in folder
			num_of_frames=len(os.listdir(f'img/{self.char_type}/{animation}'))
			for i in range(num_of_frames):
				img=pygame.image.load(f'img/{self.char_type}/{animation}/{i}.png').convert_alpha()
				img=pygame.transform.scale(img, (int(scale*img.get_width()), int(scale*img.get_height())))
				temp_list.append(img)
			self.animation_list.append(temp_list)

		self.image=self.animation_list[self.action][self.frame_index]
		self.rect=self.image.get_rect() #it takes the size of img and makes a boundary box around it, we will use it for controlling
		self.rect.center=(x,y)
		self.width=self.image.get_width()
		self.height=self.image.get_height()

	def update(self):
		self.update_animation()
		self.check_alive()
		#update cooldown
		if self.shoot_cooldown>0:
			self.shoot_cooldown-=1


	def move(self, moving_left, moving_right):
		#reset movement variables
		screen_scroll=0
		dx=0
		dy=0
		#assign movement variables if moving left or right
		if moving_left:
			dx=-self.speed
			self.flip=True
			self.direction=-1
		if moving_right:
			dx=self.speed
			self.flip=False
			self.direction=1
		#jump
		if self.jump and self.in_air==False:
			self.vel_y=-11
			self.jump=False
			self.in_air=True

		#apply gravity
		self.vel_y+=GRAVITY
		if self.vel_y>10:
			self.vel_y=10
		dy+=self.vel_y

		#check for collision
		for tile in world.obstacle_list:
			#check collision in the x direction
			if tile[1].colliderect(self.rect.x+dx, self.rect.y,self.width,self.height):
				dx=0
			#check collision in the y direction
			if tile[1].colliderect(self.rect.x, self.rect.y+dy,self.width,self.height):
				#check if below the ground ie jumping
				if self.vel_y<0:
					self.vel_y=0
					dy=tile[1].bottom-self.rect.top
				#check if above the ground ie falling
				elif self.vel_y>=0:
					self.vel_y=0
					self.in_air=False
					dy=tile[1].top-self.rect.bottom

		#check for collison with water
		if pygame.sprite.spritecollide(self, water_group, False):
			self.health=0

		#check for collison with exit
		level_complete=False
		if pygame.sprite.spritecollide(self, exit_group, False):
			level_complete=True

		#check if fallen off the map
		if self.rect.bottom > SCREEN_HEIGHT:
			self.health=0




		#check if going off the screen
		if self.char_type=='player':
			if self.rect.left +dx < 0 or self.rect.right+dx > SCREEN_WIDTH:
				dx=0
		#update rectange position
		self.rect.x+=dx
		self.rect.y+=dy	

		#update scroll based on player position
		if self.char_type=='player':
			if (self.rect.right>SCREEN_WIDTH - SCROLL_THRESH and bg_scroll < (world.level_data *TILE_SIZE) - SCREEN_WIDTH)\
			 or (self.rect.left< SCROLL_THRESH and bg_scroll > abs(dx)):
				self.rect.x-=dx
				screen_scroll= -dx

		return screen_scroll, level_complete


	def shoot(self):
		if self.shoot_cooldown==0 and self.ammo>0:
			self.shoot_cooldown=20
			bullet=Bullet(self.rect.centerx+(0.75*self.rect.size[0]*self.direction), self.rect.centery, self.direction)
			bullet_group.add(bullet)
			self.ammo-=1 #reduce ammo
			shot_fx.play()

	def ai(self):
		if self.alive and player.alive:
			if self.idling == False and random.randint(1,200)==1:
				self.update_action(0)
				self.idling=True
				self.idling_counter=50
			#check if the ai is near the player
			#DOES THE ENEMY SEE THE PLAYER? IF YES, START SHOOTING, ELSE, CONTINUE PATROLING.
			if self.vision.colliderect(player.rect):
				#stop running and face the player
				self.update_action(0)
				#shoot 
				self.shoot()
			else:
				if self.idling==False:
					if self.direction==1:
						ai_moving_right=True
					else:
						ai_moving_right=False
					ai_moving_left=not ai_moving_right
					self.move(ai_moving_left, ai_moving_right)
					self.update_action(1)
					self.move_counter+=1
					#update ai vision as the enemy moves
					self.vision.center=(self.rect.centerx+75*self.direction, self.rect.centery)
					#pygame.draw.rect(screen, RED, self.vision)

					if self.move_counter>TILE_SIZE:
						self.direction*=-1
						self.move_counter*=-1
				else:
					self.idling_counter-=1
					if self.idling_counter<=0:
						self.idling=False

		#scroll
		self.rect.x+=screen_scroll


	def update_animation(self):
		#update animation
		ANIMATION_COOLDOWN=100 #speed of animation
		#update image depending on current time
		self.image=self.animation_list[self.action][self.frame_index]
		#check if enough time has passed since the last update
		if pygame.time.get_ticks()-self.update_time > ANIMATION_COOLDOWN:
			self.update_time=pygame.time.get_ticks()
			self.frame_index+=1
		#if animation has run out reset back to the start
		if self.frame_index>=len(self.animation_list[self.action]):
			if self.action==3:
				self.frame_index=len(self.animation_list[self.action])-1
			else:
				self.frame_index=0

	def update_action(self, new_action):
		#check if the new action is different to the previous pone
		if new_action!=self.action:
			self.action=new_action
			#update the animation settings
			self.frame_index=0
			self.update_time=pygame.time.get_ticks()
	def check_alive(self):
		if self.health<=0:
			self.health=0
			self.speed=0
			self.alive=False
			self.update_action(3)


	def draw(self):
		screen.blit(pygame.transform.flip(self.image,self.flip, False), self.rect)
		#pygame.draw.rect(screen, RED, slef.rect, 1)


class World():
	def __init__(self):
		self.obstacle_list=[]

	def process_data(self,data):
		self.level_data=len(data[0])
		#iterate through each value in level data file
		for y, row in enumerate(data):
			for x, tile in enumerate(row):
				if tile>=0:
					img=img_list[tile]
					img_rect=img.get_rect()
					img_rect.x=x*TILE_SIZE
					img_rect.y=y*TILE_SIZE
					tile_data=(img, img_rect)
					if tile>=0 and tile<=8:
						self.obstacle_list.append(tile_data)
					elif tile>=9 and tile<=10:
						#water
						water=Water(img, x*TILE_SIZE,y*TILE_SIZE)
						water_group.add(water)
					elif tile>=11 and tile<=14:
						#decoration
						decoration=Decoration(img, x*TILE_SIZE,y*TILE_SIZE)
						decoration_group.add(decoration)
					elif tile==15: #create a player
						player=Combattant('player',x*TILE_SIZE,y*TILE_SIZE,1.65,5,20,5)
						health_bar=HealthBar(10,10,player.health, player.health)
					elif tile==16: #ENEMY
						enemy=Combattant('enemy',x*TILE_SIZE,y*TILE_SIZE,1.65,2,20,0)
						enemy_group.add(enemy)
					elif tile==17: #AMMO box
						item_box=ItemBox('Ammo', x*TILE_SIZE,y*TILE_SIZE)
						item_box_group.add(item_box)
					elif tile==18: #grenade box
						item_box=ItemBox('Grenade', x*TILE_SIZE,y*TILE_SIZE)
						item_box_group.add(item_box)
					elif tile==19: #Health box
						item_box=ItemBox('Health', x*TILE_SIZE,y*TILE_SIZE)
						item_box_group.add(item_box)
					elif tile==20:
						#exit
						exit=Exit(img, x*TILE_SIZE,y*TILE_SIZE)
						exit_group.add(exit)
		return player, health_bar

	def draw(self):
		for tile in self.obstacle_list:
			tile[1][0]+=screen_scroll
			screen.blit(tile[0],tile[1]) #(img, rect)


class Decoration(pygame.sprite.Sprite):
	def __init__(self,img,x,y):
		pygame.sprite.Sprite.__init__(self)
		self.image=img
		self.rect=self.image.get_rect()
		self.rect.midtop=(x+TILE_SIZE//2, y+(TILE_SIZE-self.image.get_height()))

	def update(self):
		self.rect.x+=screen_scroll


class Water(pygame.sprite.Sprite):
	def __init__(self,img,x,y):
		pygame.sprite.Sprite.__init__(self)
		self.image=img
		self.rect=self.image.get_rect()
		self.rect.midtop=(x+TILE_SIZE//2, y+(TILE_SIZE-self.image.get_height()))
	def update(self):
		self.rect.x+=screen_scroll


class Exit(pygame.sprite.Sprite):
	def __init__(self,img,x,y):
		pygame.sprite.Sprite.__init__(self)
		self.image=img
		self.rect=self.image.get_rect()
		self.rect.midtop=(x+TILE_SIZE//2, y+(TILE_SIZE-self.image.get_height()))

	def update(self):
		self.rect.x+=screen_scroll


class ItemBox(pygame.sprite.Sprite):
	def __init__(self,item_type,x,y):
		pygame.sprite.Sprite.__init__(self)
		self.item_type=item_type
		self.image=item_boxes[self.item_type]
		self.rect=self.image.get_rect()
		self.rect.midtop=(x+TILE_SIZE//2, y+(TILE_SIZE-self.image.get_height()))

	def update(self):
		#check if the player has picked up the box
		self.rect.x+=screen_scroll
		if pygame.sprite.collide_rect(self, player):
			#check what kind of box it was
			if self.item_type=='Health':
				#print(player.health)
				player.health+=25
				if player.health>player.max_health:
					player.health=player.max_health
				#print(player.health)
			elif self.item_type=='Ammo':
				player.ammo+=15
			elif self.item_type=='Grenade':
				player.grenades+=3
			#delete the item box
			self.kill()

class HealthBar():
	def __init__(self, x, y, health, max_health):
		self.x=x
		self.y=y
		self.health=health
		self.max_health=max_health

	def draw(self,health):
		#update with new health
		self.health=health
		#calculate haelth ratio
		ratio=self.health / self.max_health
		pygame.draw.rect(screen, BLACK, (self.x - 2, self.y-2, 154, 24))
		pygame.draw.rect(screen, RED, (self.x, self.y, 150, 20))
		pygame.draw.rect(screen, GREEN, (self.x, self.y, 150*ratio, 20))


class Bullet(pygame.sprite.Sprite):
	def __init__(self,x,y,direction):
		pygame.sprite.Sprite.__init__(self)
		self.speed=10
		self.image=bullet_img
		self.rect=self.image.get_rect()
		self.rect.center=(x,y)
		self.direction=direction

	def update(self):
		#move bullet
		self.rect.x+=(self.direction*self.speed)+screen_scroll
		#check if bullet have gone off screen
		if self.rect.right < 0 or self.rect.left > SCREEN_WIDTH-100:
			self.kill()
		#check for collision with level
		for tile in world.obstacle_list:
			if tile[1].colliderect(self.rect):
				self.kill()

		#check collision with characters
		if pygame.sprite.spritecollide(player, bullet_group, False):
			if player.alive:
				player.health-=5
				self.kill()
		for enemy in enemy_group:
			if pygame.sprite.spritecollide(enemy, bullet_group, False):
				if enemy.alive:
					enemy.health-=25
					self.kill()

class Grenade(pygame.sprite.Sprite):
	def __init__(self,x,y,direction):
		pygame.sprite.Sprite.__init__(self)
		self.timer=100
		self.vel_y=-11
		self.speed=7
		self.image=grenade_img
		self.rect=self.image.get_rect()
		self.rect.center=(x,y)
		self.direction=direction
		self.width=self.image.get_width()
		self.height=self.image.get_height()

	def update(self):
		self.vel_y+=GRAVITY
		dx=self.direction*self.speed
		dy=self.vel_y

		#check for collision with level
		for tile in world.obstacle_list:
			#check if bullet have gone off screen (collision with wall)
			if tile[1].colliderect(self.rect.x+dx, self.rect.y, self.width, self.height):
				self.direction*=-1
				dx=self.direction*self.speed
			#check collision in the y direction
			if tile[1].colliderect(self.rect.x, self.rect.y+dy,self.width,self.height):
				self.speed=0
				#check if below the ground ie thrown up
				if self.vel_y<0:
					self.vel_y=0
					dy=tile[1].bottom-self.rect.top
				#check if above the ground ie falling
				elif self.vel_y>=0:
					self.vel_y=0
					dy=tile[1].top-self.rect.bottom
		


		#update grenade position
		self.rect.x+=dx+screen_scroll
		self.rect.y+=dy

		#countdown timer for explosion
		self.timer-=1
		if self.timer<=0:
			self.kill()
			grenade_fx.play()
			explosion=Explosion(self.rect.x, self.rect.y, 0.5)
			explosion_group.add(explosion)
			#do damage to anyone that is nearby
			#MAKE A CHANGE HERE KI AGR TILESIZE EK UNIT HI TOH HELATH KO ZADA NUKSAAN PADEGA, YOU CAN PLAY WITH THIS BLOCK
			if abs(self.rect.centerx-player.rect.centerx) < TILE_SIZE*2 and \
				abs(self.rect.centery-player.rect.centery) < TILE_SIZE*2:
				player.health-=50
			for enemy in enemy_group:
				if abs(self.rect.centerx-enemy.rect.centerx) < TILE_SIZE*2 and \
					abs(self.rect.centery-enemy.rect.centery) < TILE_SIZE*2:
					enemy.health-=50
			
class Explosion(pygame.sprite.Sprite):
	def __init__(self,x,y,scale):
		pygame.sprite.Sprite.__init__(self)
		self.images=[]
		for num in range(1,6):
			img=pygame.image.load(f'img/explosion/exp{num}.png').convert_alpha()
			img=pygame.transform.scale(img,(int(img.get_width()*scale), int(img.get_height()*scale)))
			self.images.append(img)
		self.frame_index=0
		self.image=self.images[self.frame_index]
		self.rect=self.image.get_rect()
		self.rect.center=(x,y)
		self.counter=0

	def update(self):
		self.rect.x+=screen_scroll #scroll
		EXPLOSION_SPEED=4
		#update explosion animation
		self.counter+=1

		if self.counter>= EXPLOSION_SPEED:
			self.counter=0
			self.frame_index+=1
			#if the animation is complete then delete the explosion
			if self.frame_index>=len(self.images):
				self.kill()
			else:
				self.image=self.images[self.frame_index]

class ScreenFade():
	def __init__(self, direction, color, speed):
		self.direction=direction
		self.color=color
		self.speed=speed
		self.fade_counter=0

	def fade(self):
		fade_complete=False
		self.fade_counter+=self.speed
		if self.direction==1: #whole screen fade
			pygame.draw.rect(screen, self.color, (0-self.fade_counter,0, SCREEN_WIDTH//2, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.color, (SCREEN_WIDTH//2 + self.fade_counter,0, SCREEN_WIDTH, SCREEN_HEIGHT))
			pygame.draw.rect(screen, self.color, (0, 0 - self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
			pygame.draw.rect(screen, self.color, (0, SCREEN_HEIGHT // 2 +self.fade_counter, SCREEN_WIDTH, SCREEN_HEIGHT))
		if self.direction==2: #vertical screen fade down
			pygame.draw.rect(screen, self.color, (0,0, SCREEN_WIDTH, 0+self.fade_counter))
		if self.fade_counter >= SCREEN_WIDTH:
			fade_complete=True

		return fade_complete

#create screen fades
intro_fade=ScreenFade(1, BLACK, 4)
death_fade=ScreenFade(2, PINK, 4)

#create buttons
start_button=button.Button(SCREEN_WIDTH // 2 -130, SCREEN_HEIGHT //2 - 150, start_img, 1)
exit_button=button.Button(SCREEN_WIDTH // 2 -110, SCREEN_HEIGHT //2 + 50, exit_img, 1)
restart_button=button.Button(SCREEN_WIDTH // 2 -100, SCREEN_HEIGHT //2 - 50, restart_img, 2) #2: scale
#create sprite groups
enemy_group=pygame.sprite.Group() #container class to hold and manage multiple Sprite(visible) objects.
bullet_group=pygame.sprite.Group()
grenade_group=pygame.sprite.Group()
explosion_group=pygame.sprite.Group()
item_box_group=pygame.sprite.Group()
decoration_group=pygame.sprite.Group()
water_group=pygame.sprite.Group()
exit_group=pygame.sprite.Group()



#create empty tile list
world_data=[]
for row in range(ROWS):
	r=[-1]*COLS
	world_data.append(r)

#load in level data and create world
with open(f'LevelEditor-main/level{level}_data.csv', newline='') as csvfile:
	reader=csv.reader(csvfile, delimiter=',')
	for x, row in enumerate(reader):
		for y, tile in enumerate(row):
			world_data[x][y]=int(tile)

world=World()
player, health_bar=world.process_data(world_data)




#to make the screen running
run=True
while run:

	clock.tick(FPS) #to update the clock
	if start_game == False:
		#draw menu
		screen.fill(BG)
		if start_button.draw(screen):
			start_game=True
			start_intro=True
		if exit_button.draw(screen):
			run=False
	else:
		#update background
		draw_bg()
		#draw world map
		world.draw()
		#show player health
		health_bar.draw(player.health)
		#show ammo
		draw_text('AMMO: ', font, WHITE, 10, 35)
		for x in range(player.ammo):
			screen.blit(bullet_img, (90+(x*10),40))
		#show GRENADES
		draw_text('GRENADES: ', font, WHITE, 10, 60)
		for x in range(player.grenades):
			screen.blit(grenade_img, (135+(x*15),63))	

		player.update()
		player.draw()
		for enemy in enemy_group:
			enemy.ai()
			enemy.update()
			enemy.draw()

		#update and draw groups
		bullet_group.update()
		grenade_group.update()
		explosion_group.update()
		item_box_group.update()
		decoration_group.update()
		water_group.update()
		exit_group.update()
		bullet_group.draw(screen)
		grenade_group.draw(screen)
		explosion_group.draw(screen)
		item_box_group.draw(screen)
		decoration_group.draw(screen)
		water_group.draw(screen)
		exit_group.draw(screen)

		#show intro
		if start_intro:
			if intro_fade.fade():
				start_intro=False
				intro_fade.fade_counter=0

		#update player actions
		if player.alive: 
			#shoot bullets
			if shoot:
				player.shoot()

			#throw grenade
			elif grenade and grenade_thrown==False and player.grenades>0:
				grenade=Grenade(player.rect.centerx+(0.5*player.rect.size[0]*player.direction),\
				 				player.rect.top, player.direction)
				grenade_group.add(grenade)
				grenade_thrown=True
				player.grenades-=1

			if player.in_air:
				player.update_action(2)#2:jump
			elif moving_left or moving_right:
				player.update_action(1)#1:run
			else:
				player.update_action(0)#0: idle
			screen_scroll, level_complete=player.move(moving_left, moving_right)
			bg_scroll-=screen_scroll
			#check if player has completed the level
			if level_complete:
				start_intro=True
				level+=1
				bg_scroll=0
				world_data=reset_level()
				if level<=MAX_LEVELS:
					#load in level data and create world
					with open(f'LevelEditor-main/level{level}_data.csv', newline='') as csvfile:
						reader=csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y]=int(tile)

					world=World()
					player, health_bar=world.process_data(world_data)
				else:
					start_game=False

		else:
			screen_scroll=0
			if death_fade.fade():
				if restart_button.draw(screen):
					death_fade.fade_counter=0
					start_intro=True
					bg_scroll=0
					world_data=reset_level()
					#load in level data and create world
					with open(f'LevelEditor-main/level{level}_data.csv', newline='') as csvfile:
						reader=csv.reader(csvfile, delimiter=',')
						for x, row in enumerate(reader):
							for y, tile in enumerate(row):
								world_data[x][y]=int(tile)

					world=World()
					player, health_bar=world.process_data(world_data)

	for event in pygame.event.get():
		#quit game
		if event.type== pygame.QUIT:
			run=False
		#keyboard presses
		if event.type==pygame.KEYDOWN:
			if event.key==pygame.K_a or event.key==pygame.K_LEFT:
				moving_left=True
			if event.key==pygame.K_d  or event.key==pygame.K_RIGHT:
				moving_right=True
			if event.key==pygame.K_SPACE:
				shoot=True
			if event.key==pygame.K_q:
				grenade=True
			if (event.key==pygame.K_w or event.key==pygame.K_UP) and player.alive:
				player.jump=True
				jump_fx.play()
			if event.key==pygame.K_ESCAPE:
				run=False

		#keyboard button released
		if event.type==pygame.KEYUP:
			if event.key==pygame.K_a  or event.key==pygame.K_LEFT :
				moving_left=False
			if event.key==pygame.K_d  or event.key==pygame.K_RIGHT:
				moving_right=False
			if event.key==pygame.K_SPACE:
				shoot=False
			if event.key==pygame.K_q:
				grenade=False
				grenade_thrown=False


	pygame.display.update()

pygame.quit()
