#import "@preview/ourchat:0.1.0" as oc: default-profile

#set page(width: auto, height: auto, margin: 0em, fill: none)
#set text(font: "Microsoft YaHei")

#let parse-datetime(time-str) = {
  {
    let parts = time-str.split(" ")
    let date-parts = parts.at(0).split("-")
    let time-parts = parts.at(1).split(":")

    datetime(
      year: int(date-parts.at(0)),
      month: int(date-parts.at(1)),
      day: int(date-parts.at(2)),
      hour: int(time-parts.at(0)),
      minute: int(time-parts.at(1)),
      second: int(time-parts.at(2)),
    )
  }
}

#let time-strs = "{datetime_now}"
#let datetime_now = parse-datetime(time-strs)
#let date = datetime_now.display("[month padding:space]月[day padding:space]日  [hour]:[minute]")

#oc.chat(
  oc.datetime(date),
  oc.message(left, name: [丘成桐（囯內）], profile: default-profile)[
    {text}
  ],
)
