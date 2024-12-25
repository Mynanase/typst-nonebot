#import "@local/ourchat:0.1.0" as oc: default-profile

#set page(width: auto, height: auto, margin: 1em, fill: none)
#set text(font: "Microsoft YaHei")

#oc.chat(
  oc.message(left, name: [丘成桐（囯內）], profile: default-profile)[
    {text}
  ],
)