#set page(
    width: auto,
    height: auto,
    margin: (x: 8pt, y: 12pt)
)

#set text(font: "Buenard", fill: white, size: 32pt)
//#set text(stroke: white)
#set text(weight: "black")
#set page(
  fill: gradient.linear(
    rgb(50, 143, 185),
    rgb(42, 170, 165),
    rgb(30, 179, 180),
  ),
)
#let rainbow(content) = {
  set text(fill: gradient.linear(..color.map.rainbow))
  box(content)
}

{group_name}

#rainbow[欢迎新人 {name}]