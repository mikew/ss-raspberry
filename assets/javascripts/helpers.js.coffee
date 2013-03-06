unless Array::filter
  Array::filter = (callback) -> element for element in this when callback(element)

globals      = window
globals._d   = (lines...) -> console? && console.log line for line in lines
globals._app = {}

globals._dattr = (e, a, v) ->
  n = "data-#{a}"

  e.setAttribute n, v if v?
  e.getAttribute n
