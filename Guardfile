require 'coffee-script'
require 'sprockets'
require 'sprockets-sass'
require 'sass'
require 'compass'

ROOT = File.expand_path '../', __FILE__

def sprocket_env
  asset_paths = %w[
    assets/javascripts
    assets/stylesheets
    assets/images
    vendor/javascripts
    vendor/stylesheets
    vendor/images
  ]

  Compass.configuration do |config|
    config.project_path = ROOT
    config.sass_dir     = 'assets/stylesheets'
    config.css_dir      = 'assets/stylesheets'
    config.images_dir   = 'public/images'
  end

  environment = Sprockets::Environment.new File.dirname(__FILE__)
  asset_paths.each {|path| environment.append_path path }

  environment.context_class.class_eval do
    def asset_path(path, options = {}) "/images/#{path}" end
    def image_path(path, options = {}) super(path)       end
  end

  environment
end

guard 'coffeescript', input: 'assets/javascripts', output: 'public/assets' do
  watch(%r{^assets/.*\.coffee$})
end

guard 'sprockets2',
  sprockets:  sprocket_env,
  digest:     false,
  gz:         false,
  precompile: [/\w+\.(?!js|css|scss|sass|coffee).+/, /application.(css|js)$/ ] do

  watch(%r{^assets/(images|javascripts|stylesheets)/.+$})
  #watch(%r{^assets/.+$})
end
