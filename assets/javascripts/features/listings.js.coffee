class App.Views.Listings_endpoint extends Backbone.View
  tagName  : 'article'
  template : JST['templates/listings_endpoint']

  events:
    'click' : 'navigate'

  navigate: =>
    _app.navigate "/e/#{@model.endpoint}", trigger: true

  render: ->
    template = @template @model
    @$el.html template

    return this

class App.Views.Listings_episode extends App.Views.Listings_endpoint
  template : JST['templates/listings_episode']
  events:
    'click' : 'play'

  play: =>
    $.get "/play/#{@model.endpoint}"

class App.Views.Listings_movie extends App.Views.Listings_episode

class App.Features.Listings extends Backbone.View
  fetch: (endpoint, title) ->
    $.getJSON "/payload/#{endpoint}", (data, status) => @parse data, title

  parse: (data, title) =>
    title = data.title or title
    items = data.items or []

    for item in data.items
      view = @view_from_item item
      @$el.append view.render().el

  view_from_item: (item) ->
    type = item._type
    delete item._type
    new App.Views["Listings_#{type}"] model: item
