---
raw_path: raw/youtube/how-to-reverse-engineer-any-software-in-minutes-HLsMMsvPDLY.md
content_hash: 2a209a3db399b77baf2a8c456836b90360feb80243fa6dfd6de61a009d16c0b7
title: How To Reverse Engineer Any Software in Minutes
---

<!-- t: 00:00 -->

You can now reverse engineer anything using this GitHub repo that just got 170,000 stars. Maybe you're tired of paying Adobe a monthly subscription to use Photoshop. Well, this guy just reverse engineered the whole Adobe suite from Photoshop to Illustrator to Premiere Pro, even After Effects. But, what's interesting about this is that it works on desktop apps, games, web apps, even mobile apps. So, you can create clones of your favorite apps that runs free and

<!-- t: 00:32 -->

locally. You don't need to know how to code. So, I'm going to show you what Ria is, how it works, and how I managed to create a one-to-one clone of TikTik in just a prompt. So, what is Ria and why should you care? Well, before Ria, if we wanted to reverse engineer an app, we would take the app, you would do some screenshots and prompts, and AI would guess at what all the buttons do, and the app that you make looks very close. And then, you would probably screenshot

<!-- t: 01:05 -->

and prompt it again to make another app, and you would keep going in that loop on your own. But, what Ria does is that it looks at the app itself, and it will actually read the app down to its binary code. This is something only machines really look at because it's only ones and zeros, and this step is called decompiling. This is something way too tedious for humans to do, but AI that doesn't sleep, doesn't need food, can

<!-- t: 01:36 -->

just keep decompiling the software into readable code. So, all it's doing is looking for evidence of this code being correct, and by the end, you have your own version. So, this works even if the code is not open source, it's a closed source project because of the step of decompilation. Now, how this works in reality is that you use it inside of Claude code or Codex or whatever your harness is, you just download one RE

<!-- t: 02:07 -->

MCP, and that's going to use any of these different tools like Hopper, Ghidra, and IDA for desktop apps, JS analyzer for electron apps and JavaScript, browser for web apps, JADX for Android apps and so forth. And all it's trying to do is decompile where it needs to to get evidence of what the code is saying like on the machine code binary level, it will find evidence,

<!-- t: 02:38 -->

logic, how the functions work, and so forth. Then it builds it, and it keeps going in a loop asking sharper and sharper questions until the app is basically rebuilt. Some of this can take 12 minutes. Some of them can take six whole days if you're decompiling, for example, Nintendo 64 games that some teams have tried to spend five years doing manually themselves, and that's why the whole internet is now saying

<!-- t: 03:08 -->

that you'll own everything for free and be happy compared to all the subscription models where it was you'll own nothing and you'll be happy. But, we'll get into the nuances of this in just a second in a later stage. But, now you might be asking, "How can you actually set this up?" So, to get access, all you need to do is to go to this repo right here called RE. As you can see, it's just one command to get this installed. So, we're just going to

<!-- t: 03:40 -->

copy this right here, and we're going to go back into Claude or Codex or whatever agent that you're running. If this is completely new to you, make sure that you're not in the chat version, but in the coding session. Don't worry, we're not going to code anything, but we'll start by asking it, "Can you set this up for me?" Send it. If you're more confident running it in the terminal, you can also do it like this, where you set it up. You just click Y, and it will install it on your computer. Just like

<!-- t: 04:10 -->

that, we have installed reverse engineer anything. Now, the second thing that might happen when you're installing it is that you get this Hopper Disassembler installed as well, and you don't have to purchase a license. You can just try the demo, as this will be the app that will actually use to do the decompiling. Now that you have everything installed, let's go to the next step, and that's choosing the app you want to reverse engineer. For this example, we're going to use TickTick, which millions of people use to capture ideas, organize

<!-- t: 04:42 -->

life, and do something creative. It's basically a to-do list and project management app that I believe is the favorite of MKBHD, Marques Brownlee, the tech reviewer. So, now that you figured out which app you actually want to use, you can see the prompt here is find TickTick on my Mac, use Ria to figure out the whole app, the task list, the calendar, the timeline, how everything fits together. Show me the evidence you find in the app files. Don't change anything in TickTick itself, then build

<!-- t: 05:13 -->

me my own version called TaskYard with sample tasks to start. And underneath that, I gave the ground rules. Only read TickTick, never change it. Don't copy its icons, make new ones. Write every findings to an evidence file with where it came from, and build a real Mac app that compiles and runs. If you want to run this yourself, just change out TickTick to the app of your choice, and then ask Claude to rewrite the prompt, so it's not just a task list, a calendar, and everything like that. Now,

<!-- t: 05:44 -->

just click on enter, and it's going to start doing the whole process. Now, I already did this yesterday with the exact same prompt. Now, what ended up happening for me is that Hopper started going, and you can see how it looked like here. This is how the decompiling looks like. It's trying to read it, and then actually make it into agent-written code. But, AI just kept working, and Taskade was built and open on my screen in only 12 minutes, and it took $3.92

<!-- t: 06:17 -->

of API rate equivalent. So, it didn't actually cost much at all. So, I checked the app, and it was very close to what I actually got. But, I saw that when I clicked on the to-do list item, it didn't actually make a pling sound. There was a couple of features that was missing that I've gotten used to from TickTick. But, one thing that happened during this step was that Hopper actually quit unexpectedly. And so, it didn't actually do the decompiling and

<!-- t: 06:48 -->

writing good code. And so, I wanted to see if I can use this other app, which is called Ghidra, that is actually decompiled, and I would call it TaskFlow instead. This kept going back and forth and back and forth. You can see that the decompiling was done. The app was now on my computer as TaskFlow, and it took 56 minutes and cost only $19 at API rates. Of course, since I have a subscription, that was a way less than that. And you

<!-- t: 07:18 -->

can even see what the decompiled code showed, like quick add, morning means 9, evening 5, priority stored as 0, 1, 3, and 5, status 0 means open. And so, this all gave it a lot better context than our previous method of just giving screenshots and prompts. And this is the app that we ended up with. So, now let's look at the comparison. As you can see, we have TickTick on the left side and we have my task flow here on the right

<!-- t: 07:49 -->

side. It has the task like call the dentist to reschedule right here as well. Pick up dry cleaning. And if I click on one of them as done, as you can see, it goes down to the completed. Here as well, pick up the dry cleaning, we get a different sound and it goes directly down to the completed tab. You can also see that we have the list here of business, work, personal, fitness, and everything like that. The exact same goes in my app as well. And

<!-- t: 08:21 -->

if we keep going further down, you can see that we have all the tags, errands, family, finance, and everything like that, which is just a tagging or a hashtag system that is working really great. Just look at errands on both of them. We can click here, click here, and it looks almost identical. Let's try to add a task like do laundry. It pops up right there. Here as well, let's do do laundry. It pops up here as well with a different type of hashtag in the

<!-- t: 08:53 -->

beginning there to really show where it lands. But then I found out something that actually shocked me. So, I don't have the paid version of TickTick. And it's so if we click on the calendar view on the side here, it says you have to upgrade now. But on my own app here, if I just open the side, you can see that I click on the calendar view and I actually have full access to it. So, REA was actually able to reverse engineer the calendar view as well, even without

<!-- t: 09:23 -->

having access to it because it's written in the code. So, here you can see that the premium only does this sample data, and this is actually real data, which is just absolutely crazy that it was able to do this without looking at the source code just from the machine binary. But But, I also want to talk to you about the negatives. So, for example, there are some features that aren't included. Like, for example, if I click on do laundry right here, we have a really nice way of writing in the right side.

<!-- t: 09:55 -->

Whereas, if I click on do laundry here, we are only able to actually write in one line. If I click enter, it kind of goes back to the beginning here, and I'm not able to create a new line. And so, this is where we would have to prompt it again to do that well. The same goes for if we're on today, for example, the colors aren't completely correct. You can see here the overdue is white. Here, the overdue is actually red, and even the completed ones still has a color. In

<!-- t: 10:27 -->

the real TickTick, they have this countdown page. Whereas, we don't actually have a countdown page here in our TickTick version. And the same goes for search, as well. It's right here, so we can search for any task. We don't have that in our version, either. Lastly, the number one issue that I found was that if you do one-on-one with Jonas, and you actually right-click on the real app, you can see that we have today, tomorrow, next week, and so forth, that you have this whole menu.

<!-- t: 10:59 -->

Whereas, if we do that on the cloned app, you can see that we don't actually have that much of the features included in our app. So, it comes a bit short, and that's where you have to, for example, take a screenshot and say, "Can you make features like this?" But, here is the most important part of the whole experience here. We're able to pretty much reverse the whole app in about an hour, give or take some extra prompts just to get it to a final state. But,

<!-- t: 11:31 -->

the main thing that I really want you to get out of this is this is almost 80% of the whole app. And the main benefit of, of course, having your own app like this is that you don't have to pay for it. But, the main benefit being that you can build on top of it. So, I actually have my own personal to-do app, which is called Goalflow. This is something I vibe coded about 2 months ago, and it took way longer time to build this than the app that I just showed you. But, here is

<!-- t: 12:02 -->

what I want to show you. So, take a look at this. If I right-click on, for example, Goalflow Upgrades, one of the main key differences that I wanted to have is that you could click on send to agent. >> [music] >> And if I click on that, it actually sends that task directly to Claude code, so it can do the task for me. If you have a closed-source app like TickTick, and I right-click, and I want that feature, the only way to get that feature is to ask customer support,

<!-- t: 12:34 -->

"Hey, can I ask for a feature request?" And then they might do it or might definitely not do it because it actually hurts more than it helps to just add a bunch of to it. And so, beyond the payment itself, the main benefit is that you can customize it however it fits you. You can build on top of it, so it becomes the ultimate productivity system for you. Software as we know it is no longer one software company that just makes one software that fits a million

<!-- t: 13:06 -->

people. It's that you can have your own version, and you can make it your own private, local, and free version for your specific use case. And if you want to go deeper on this, I highly recommend going to our school community and checking out the 7-day AI build series, where you will get your first app up and running in no time, specifically made for you or for your clients. Thank you so much for watching the video and I'll see you in the next one. Peace.
