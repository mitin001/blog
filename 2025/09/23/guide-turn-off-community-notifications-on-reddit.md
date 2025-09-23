# Guide: turn off community notifications on Reddit

You go on Reddit, and you see a red dot on the bell icon, indicating that you have a notification. Surely this means someone has reacted to something you posted. This feels good. You get a dopamine hit. Until you actually check to see what the notification is. You open your [notifications] and find that it was simply an ad for you to go check some post you don't care about.

<img width="862" height="244" alt="image" src="https://github.com/user-attachments/assets/30ebb9dc-51f9-422a-8144-26a1494bbcf3" />

You are confused. This is not the main page. Why are you getting other people's content in your notification feed? The notification feed should be telling you if people have been interacting with your content, not advertising other people's content. It's time to turn these notifications off. Head on to [notification settings]. When you open community notifications, you see that you're subscribed to all kinds of crap, and there's no button to turn all this off at once. Clicking all these buttons requires way too much mouse movement for my liking. Mouse movement requires too much precision, too much attention, too much work. I'd rather hit a few keys on the keyboard, even if repetitively. It's much faster as it does not require much precision or attention.

<img width="862" height="793" alt="image" src="https://github.com/user-attachments/assets/a1490452-328f-4f1f-8dce-31c48420399b" />

Here's how to click all the Off buttons without involving the mouse too much. Open up Developer Tools.

<img width="862" height="519" alt="image" src="https://github.com/user-attachments/assets/d0a36b22-24c4-42da-8aed-f56c2eb6a2fb" />

On the console, run the following JS command:

```js
document.querySelector('#community-notifications div.gap-xs button:nth-child(1):not([rpl-selected])').click();
```

(Syntax references: [document.querySelector], [selectors], [attribute selectors], [click]).

<img width="864" height="126" alt="image" src="https://github.com/user-attachments/assets/dd1b0290-04a3-4642-97e3-afb8fe6c529e" />

This clicked the Off button for you on the first community.

<img width="862" height="235" alt="image" src="https://github.com/user-attachments/assets/1a089db1-60c3-4325-bf1a-e36390c45b92" />

Now, hit the following keys on the keyboard: Up, Enter.

<img width="864" height="202" alt="image" src="https://github.com/user-attachments/assets/2f5fcb60-fb5b-47b2-b02b-c48ad1f8bcc3" />

This instructed the console to find the last command (Up) and run it again (Enter). And so the second Off button has been clicked without you having to locate it with your mouse.

<img width="863" height="270" alt="image" src="https://github.com/user-attachments/assets/a61ce226-83ee-4cff-b3cc-6a87f96926d5" />

Keep clicking Up, Enter, Up, Enter, Up, Enter, ...

<img width="864" height="655" alt="image" src="https://github.com/user-attachments/assets/726d5f4e-bea5-418d-a1fd-d4c3d39baf00" />

...until you're unsubscribed from all the community notifications.

<img width="862" height="629" alt="image" src="https://github.com/user-attachments/assets/282ee70e-8fda-4e68-b7d1-94f0710f49cf" />

You're welcome.

[notifications]: https://www.reddit.com/notifications
[notification settings]: https://www.reddit.com/settings/notifications
[document.querySelector]: https://developer.mozilla.org/en-US/docs/Web/API/Document/querySelector
[selectors]: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_selectors
[attribute selectors]: https://developer.mozilla.org/en-US/docs/Web/CSS/Attribute_selectors
[click]: https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/click
