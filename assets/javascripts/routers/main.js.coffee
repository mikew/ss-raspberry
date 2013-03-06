#= require_tree ../features

class App.Routers.Main extends Backbone.Router
  features: {}

  routes:
    'e/*path'  : 'listings_fetch'
    '*default' : 'index'

  initialize: ->
    to_load =
      #Player   : '#player'
      Listings : '#listings'

    for key, selector of to_load
      @features[key.toLowerCase()] = new App.Features[key] el: $(selector)

  set_title: (new_title) ->
    default_title  = 'SS Pi'
    document.title = (new_title && "#{new_title} | #{default_title}") || default_title

  index: ->
    @features.listings.fetch '/'

  listings_fetch: (endpoint) ->
    @features.listings.fetch endpoint
