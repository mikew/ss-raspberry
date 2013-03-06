#= require_self
#= require helpers
#= require_tree ./templates
#= require routers/main

window.App =
  Models      : {}
  Collections : {}
  Views       : {}
  Routers     : {}
  Features    : {}

  init: ->
    window._app = new App.Routers.Main()
    Backbone.history.start(pushState: true)

$(document).ready ->
  App.init()
