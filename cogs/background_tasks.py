import discord
from discord.ext import commands, tasks
from discord.utils import get

import time
import os
import mysql.connector
from dotenv import load_dotenv
load_dotenv()

class backgroundTasks(commands.Cog):

  def __init__(self, client):
    self.client = client
    self.db_host = os.getenv('db_host')
    self.db_username = os.getenv('db_username')
    self.db_password = os.getenv('db_password')
    self.db_name = os.getenv('db_database_name')

    self.options = {
      'usersync': self.userSync,
    }

    self.guild_id = os.getenv('guild_id')
  
  @commands.Cog.listener()
  async def on_ready(self):
    for a in self.options:
      try:
        self.options[a].start()
      except Exception as e:
        pass
              
  @tasks.loop(seconds=60)
  async def userSync(self):
    conn = mysql.connector.connect(
      host=str(self.db_host),
      user=str(self.db_username),
      password=str(self.db_password),
      database=str(self.db_name),
    )
    c = conn.cursor()

    query = "SELECT * FROM discord_data"
    c.execute(query)
    discord_data = c.fetchall()

    query = "SELECT * FROM users"
    c.execute(query)
    user_data = c.fetchall()

    query = "SELECT * FROM mentors"
    c.execute(query)
    all_atc_mentors = c.fetchall()
    atc_mentors_ids = [];
    for m in all_atc_mentors:
      atc_mentors_ids.append(m[0])

    guild = self.client.get_guild(int(self.guild_id))
    users = guild.members

    atc_rank_roles = {
      "2": get(guild.roles, id=int(os.getenv('r_s1'))),
      "3": get(guild.roles, id=int(os.getenv('r_s2'))),
      "4": get(guild.roles, id=int(os.getenv('r_s3'))),
      "5": get(guild.roles, id=int(os.getenv('r_c1'))),
      "7": get(guild.roles, id=int(os.getenv('r_c3'))),
      "8": get(guild.roles, id=int(os.getenv('r_i1'))),
      "10": get(guild.roles, id=int(os.getenv('r_i3'))),
    }
    rankS1 = get(guild.roles, id=int(os.getenv('r_s1')))
    rankS2 = get(guild.roles, id=int(os.getenv('r_s2')))
    rankS3 = get(guild.roles, id=int(os.getenv('r_s3')))
    rankC1 = get(guild.roles, id=int(os.getenv('r_c1')))
    rankC3 = get(guild.roles, id=int(os.getenv('r_c3')))
    ranki1 = get(guild.roles, id=int(os.getenv('r_i1')))
    ranki3 = get(guild.roles, id=int(os.getenv('r_i3')))

    atc_role = get(guild.roles, id=int(os.getenv('r_atc')))
    member_role = get(guild.roles, id=int(os.getenv('r_member')))
    guest_role = get(guild.roles, id=int(os.getenv('r_guest')))
    atc_mentor = get(guild.roles, id=int(os.getenv('r_mentoratc')))
    pilote_mentor = get(guild.roles, id=int(os.getenv('r_mentorpilot')))

    staff_role = get(guild.roles, id=int(os.getenv('r_staff')))

    member_list = []
    for d in discord_data:
      member_list.append(int(d[2]))
      for u in user_data:
        if u[0] == d[1]:
          print(f"Linked user found - Name: {u[2]} {u[3]}")
          for us in users:
            foundUser = False
            if us.id == int(d[2]):
              foundUser = True

              # Assign member role and remove guest role
              if guest_role in us.roles:
                await us.remove_roles(guest_role)
              if not member_role in us.roles:
                await us.add_roles(member_role)

              print(f"User found: {us.id}")
              username = f"{u[2]} - {u[9]}"
              user_atc_rank = u[8]

              # Take care of ATC roles, remove unneeded and add needed
              if user_atc_rank in atc_rank_roles:
                if not atc_role in us.roles:
                  await us.add_roles(atc_role)
                
                for ar in atc_rank_roles:
                  if ar == user_atc_rank and not atc_rank_roles[ar] in us.roles:
                    await us.add_roles(atc_rank_roles[ar])
                  if ar != user_atc_rank and atc_rank_roles[ar] in us.roles:
                    await us.remove_roles(atc_rank_roles[ar])
              
              else:
                if atc_role in us.roles:
                  await us.remove_roles(atc_role)
                
                for ar in atc_rank_roles:
                  if ar == user_atc_rank and not atc_rank_roles[ar] in us.roles:
                    await us.add_roles(atc_rank_roles[ar])
                  if ar != user_atc_rank and atc_rank_roles[ar] in us.roles:
                    await us.remove_roles(atc_rank_roles[ar])
              
              # Add / remove atc mentor role & staff role
              if u[0] in atc_mentors_ids:
                if not atc_mentor in us.roles:
                  await us.add_roles(atc_mentor)
                if not staff_role in us.roles:
                  await us.add_roles(staff_role)
              else:
                if atc_mentor in us.roles:
                  await us.remove_roles(atc_mentor)
                if staff_role in us.roles:
                  await us.remove_roles(staff_role)
          
              # edit user's display name / nickname
              try:
                if not us.display_name == username:
                  await us.edit(nick=username)
              except Exception as e:
                pass              

    for u in users:
      if not u.id in member_list:
        print(f"{u.display_name} linked")
        if not guest_role in u.roles:
          print(f"Gave guest to {us.display_name}")
          await u.add_roles(guest_role)
        if member_role in u.roles:
          await u.remove_roles(member_role)
    
    c.close()
    print(f"Done.")

def setup(client):
    client.add_cog(backgroundTasks(client))