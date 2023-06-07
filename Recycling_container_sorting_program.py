import sys
sys.path.append('../')
from Common.project_library import *

# Modify the information below according to you setup and uncomment the entire section

# 1. Interface Configuration
project_identifier = 'P3B' # enter a string corresponding to P0, P2A, P2A, P3A, or P3B
ip_address = '172.20.10.2' # enter your computer's IP address
hardware = False # True when working with hardware. False when working in the simulation

# 2. Servo Table configuration
short_tower_angle = 315 # enter the value in degrees for the identification tower 
tall_tower_angle = 90 # enter the value in degrees for the classification tower
drop_tube_angle = 180 #270 enter the value in degrees for the drop tube. clockwise rotation from zero degrees

# 3. Qbot Configuration
bot_camera_angle = -21.5 # angle in degrees between -21.5 and 0

# 4. Bin Configuration
# Configuration for the colors for the bins and the lines leading to those bins.
# Note: The line leading up to the bin will be the same color as the bin 

bin1_offset = 0.20 # offset in meters
bin1_color = [1,0,0] # e.g. [1,0,0] for red
bin2_offset = 0.20
bin2_color = [0,1,0]
bin3_offset = 0.20
bin3_color = [0,0,1]
bin4_offset = 0.20
bin4_color = [0,0,0]

#--------------- DO NOT modify the information below -----------------------------

if project_identifier == 'P0':
    QLabs = configure_environment(project_identifier, ip_address, hardware).QLabs
    bot = qbot(0.1,ip_address,QLabs,None,hardware)
    
elif project_identifier in ["P2A","P2B"]:
    QLabs = configure_environment(project_identifier, ip_address, hardware).QLabs
    arm = qarm(project_identifier,ip_address,QLabs,hardware)

elif project_identifier == 'P3A':
    table_configuration = [short_tower_angle,tall_tower_angle,drop_tube_angle]
    configuration_information = [table_configuration,None, None] # Configuring just the table
    QLabs = configure_environment(project_identifier, ip_address, hardware,configuration_information).QLabs
    table = servo_table(ip_address,QLabs,table_configuration,hardware)
    arm = qarm(project_identifier,ip_address,QLabs,hardware)
    
elif project_identifier == 'P3B':
    table_configuration = [short_tower_angle,tall_tower_angle,drop_tube_angle]
    qbot_configuration = [bot_camera_angle]
    bin_configuration = [[bin1_offset,bin2_offset,bin3_offset,bin4_offset],[bin1_color,bin2_color,bin3_color,bin4_color]]
    configuration_information = [table_configuration,qbot_configuration, bin_configuration]
    QLabs = configure_environment(project_identifier, ip_address, hardware,configuration_information).QLabs
    table = servo_table(ip_address,QLabs,table_configuration,hardware)
    arm = qarm(project_identifier,ip_address,QLabs,hardware)
    bins = bins(bin_configuration)
    bot = qbot(0.1,ip_address,QLabs,bins,hardware)
    

#---------------------------------------------------------------------------------
# STUDENT CODE BEGINS
#---------------------------------------------------------------------------------

import random
import time

speed_factor = 0.5 #Speed factor that allows for the speed of the bot to be adjusted easily 

dispensed_container = ["Material", 0, "Bin#"] #Variable that keeps track of the first dispensed container per round trip
new_container = ["Material", 0, "Bin#"] #Variable that keeps track of the last dispensed container on the rotary machine 

container_count = 0 #Variable that keeps count of the number of variables loaded on the container at the time 
total_container_weight = 0 #Variable that keeps count of the total mass on the qbot at the time 

bot_start_position = [0, 0, 0]

def move_container():
    global total_container_weight
    global container_count

    #Define all the pick-up and drop-off locations
    pick_up_location = [0.638, 0, 0.253]
    drop_off_location_1 = [-0.118, -0.511, 0.669]
    drop_off_location_2 = [-0.028, -0.523, 0.669]
    drop_off_location_3 = [0.054, -0.522, 0.669] 
    desired_drop_off_location = [0, 0, 0]

    #Determine the correct desired drop off location based on the container count (Ex. if this is the third container being added, place the container in the left most position)
    if container_count == 0:
        desired_drop_off_location = drop_off_location_1
    elif container_count == 1:
        desired_drop_off_location = drop_off_location_2
    elif container_count == 2:
        desired_drop_off_location = drop_off_location_3

    arm.move_arm(pick_up_location[0], pick_up_location[1], pick_up_location[2]) #Move the q-arm to the pick up location
    time.sleep(1)
    arm.control_gripper(35) #Grab the container 
    time.sleep(1.5)
    arm.rotate_elbow(-10)
    time.sleep(0.5)
    arm.move_arm(desired_drop_off_location[0], desired_drop_off_location[1], desired_drop_off_location[2]) #Move to the desired drop off location 
    time.sleep(1.5)
    arm.rotate_elbow(25)
    time.sleep(1)
    arm.control_gripper(-15) #Drop off the container
    container_count = container_count + 1 #Increase the container count by 1
    total_container_weight = total_container_weight + (int)(dispensed_container[1]) #Add the contianer weight to the total mass on the q-bot
    time.sleep(1.5)
    arm.rotate_elbow(-30)
    time.sleep(1.5)
    arm.home() #return to home position
    time.sleep(1)
    

def load_containers(): #Inputs and outputs nothing. This function loads the bot with upto 3 containers based on certain criteria (drop-off bin, total mass on bot, number of containers on bot) and then stops. 
    global dispensed_container
    global new_container
    global container_count
    global total_container_weight

    arm.home() #Reset the position of the arm 
    time.sleep(0.5)
    bot.rotate(95) #Rotate bot to allow for easier loading 
    time.sleep(1)

    #Move the first container that was already on the rotater
    if container_count == 0:
        move_container()

    #While loop that keeps running as long as the three loading conditions are met
    load_another_container = True
    while load_another_container:
        new_container = table.dispense_container(random.randint(1, 6), True) #Spawn a new random container 
        if new_container[2] == dispensed_container[2] and total_container_weight + (int)(new_container[1]) <= 90 and container_count < 3: #Check if the new container would satisfy the three conditions if loaded
            move_container() #Load the new container on the bot as well since it still satisfies the three conditions 
        else:
            load_another_container = False #Set this boolean to false to break the while loop since the new container cannot be loaded on 
    
    bot.rotate(-98) #Rotate the bot back to its original rotation
    time.sleep(0.5)


def move_robot(): #Inputs and outputs nothing. This function makes the bot follow the line until the drop off container is found. 
    global dispensed_container
    global speed_factor
    global bot_start_position

    bot_start_position = bot.position() #Update the starting positon of the bot before it starts its loop around the track 

    target_colour = [1, 0, 0] #Create a variable that stores the rgb values for the colour of the target bin
    #Series of if and elif statements that update the target colour the bot is searching for based on the target bin 
    if dispensed_container[2] == "Bin01":
        target_colour = [1, 0, 0]
    if dispensed_container[2] == "Bin02":
        target_colour = [0, 1, 0]
    if dispensed_container[2] == "Bin03":
        target_colour = [0, 0, 1]
    if dispensed_container[2] == "Bin04":
        target_colour = [0, 0, 0]

    #Activate the color and ultrasonic sensors 
    bot.activate_color_sensor()
    bot.activate_ultrasonic_sensor()

    #Store the inital colour and distance readings of the robot into variables 
    read_colour = bot.read_color_sensor() 
    read_distance = bot.read_ultrasonic_sensor()
    
    while read_colour != target_colour or read_distance > 0.10: #While loop keeps running until there is an object in the near 10 centimeters and its colour matches the target_colour the bot is looking for 
        #Series of if and elif statements that set the bot's wheel speeds accordingly based on the positioning of the yellow line on its sensor. This effectively allows it to follow the yellow line. 
        if bot.line_following_sensors() == [1, 1]:
            bot.set_wheel_speed([0.1 * speed_factor, 0.1 * speed_factor])
        elif bot.line_following_sensors() == [1, 0]:
            bot.set_wheel_speed([0.1 * speed_factor, 0.18 * speed_factor])
        elif bot.line_following_sensors() == [0, 1]:
            bot.set_wheel_speed([0.18 * speed_factor, 0.1 * speed_factor])
        elif bot.line_following_sensors() == [0, 0]:
            bot.set_wheel_speed([-0.1 * speed_factor, 0.1 * speed_factor])
            print("Lost the line")
            
        read_colour = bot.read_color_sensor()[0] #Update the colour reading to the current reading by the sensor
        read_distance = bot.read_ultrasonic_sensor() #Update the distance reading to the current reading by the sensor

    #Deactivate colour and ultrasonic sensors 
    bot.deactivate_color_sensor()
    bot.deactivate_ultrasonic_sensor()


def dump_containers(): #Inputs and outputs nothing. This function moves the container closer to the bin and drops off the containers. 
    global container_count
    global total_container_weight
    
    bot.forward_distance(0.1) #Move the bot towards the bin (the bot typically stops at the start of the bin since that's when it's sensors first align with the box and we want the robot to drop off the container in the middle of the box)
    #bot.rotate(20) #Rotate the bot the align itself with the bin (the rotation isn't always needed, but it helps when it is needed, and doesn't impact performance when it is not needed)
    bot.stop()
    time.sleep(1)

    #Initiate the drop off mechanism to drop the containers into the bin
    bot.activate_linear_actuator()
    bot.dump()
    bot.deactivate_linear_actuator()

    #Reset the container weight and container count to their default values since the current containers have been dropped off
    total_container_weight = 0
    container_count = 0


def return_home(): #Inputs and outputs nothing. This function makes the bot follow the yellow line until it arrives back to its home position 
    global dispensed_container
    global speed_factor
    global bot_start_position
    
    current_position = bot.position() #Gets the current position of the bot 
    home_check = False
    
    while home_check == False:
        #Series of if and elif statements that set the bot's wheel speeds accordingly based on the positioning of the yellow line on its sensor. This effectively allows it to follow the yellow line. 
        if bot.line_following_sensors() == [1, 1]:
            bot.set_wheel_speed([0.1 * speed_factor, 0.1 * speed_factor])
        elif bot.line_following_sensors() == [1, 0]:
            bot.set_wheel_speed([0.1 * speed_factor, 0.18 * speed_factor])
        elif bot.line_following_sensors() == [0, 1]:
            bot.set_wheel_speed([0.18 * speed_factor, 0.1 * speed_factor])
        elif bot.line_following_sensors() == [0, 0]:
            bot.set_wheel_speed([-0.1 * speed_factor, 0.1 * speed_factor])
            print("Lost the line")
            
        current_position = bot.position() #Updates the current position of the bot
        if abs(current_position[0] - bot_start_position[0]) <= 0.05 and abs(current_position[1] - bot_start_position[1]) <= 0.05 and abs(current_position[2] - bot_start_position[2]) <= 0.05: #Check to see if the current positon of the bot is equal to the starting position of the bot 
            home_check = True #Sets the boolean variable to true which breaks the while loop 

    bot.forward_distance(0.05) #Move the bot forward a bit to help adjust its positon
    bot.rotate(5) #Rotae the bot a bit to help adjust its position 
    print("Arrived Home. Mission Complete Commander!") #Print a fun little mission complete message :)
    bot.stop()
    

def main():
    global dispensed_container
    dispensed_container = table.dispense_container(random.randint(1, 6), True) #Dispense the first container

    #While loop that keeps the container spawn and drop off process running forever 
    while True:
        load_containers()
        move_robot()
        dump_containers()
        return_home()
        dispensed_container = new_container #Set the current container values to the values of the rejected conainter from the first run 

main() #Call the main function and start the overall loop

#---------------------------------------------------------------------------------
# STUDENT CODE ENDS
#---------------------------------------------------------------------------------
