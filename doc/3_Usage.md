[< Previous step](2_Codebase_Overview.md) | [Home](../README.md) | [Next step >](4_Application_Flow.md)

---
# Usage

## Starting the bot
First, clone or update your local repositiory. You can either using the command line or a user interface like [Fork](https://git-fork.com) or [GitKraken](https://gitkraken.com) (recommended).
- Command line
  - To clone: `git clone link_to_repo`
  - To update: `git pull origin master`

Second, you have to create or update the environment. 
- To create it: `conda env create -f enviroment.yml`
- To update it `conda env update --file environment.yml  --prune`

Third, activate the environment.
- On Windows: `activate all`
- On Linux / MacOS: `conda activate all`

Finally, start the bot.
- Start the bot: `python main.py bot.config`
- Start the test bot: `python main.py test_bot.config`


The first time you start the bot, you are asked to enter your phone (or bot) token. What do you have to enter?
Enter the phone number that is specified in the config-file under telegram_api.phone_number. 
You will then be asked to enter a code that you have received. 
To do this you must ask someone who has access to the phone number to give you the code. 



---
## Once the bot is running
If you have successfully started the bot, you are now ready to begin the conversation. \
Which path to go depends on if you are already in a group or if you want to start from the very beginning.

### You don't have a group yet?
In order to get access to a group, text the bot in a private message `/start`.\
This will initialize the procedure of the group creation and access management. Follow the steps of the bot and you will be put in a group and are ready to go!

### When you already are in a group
Once the bot is running, you can start the conversation by writing the message `/start` in telegram to the bot. 

### Stopping the conversation
If you want to cancel the private conversation or the escape mission at any time, simply write ``/stop`` and the bot will 
end the conversation. If you are in the middle of a language task, you might have to write ``/stop`` twice.

### Stopping the bot
If you, for any reason, want to force a shut down of the bot, go to your console where the bot is running and 
press the buttons ``CTRL`` + `C` for force quit the running bot.