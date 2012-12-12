import os

from pyramid.config import Configurator
from pyramid.session import UnencryptedCookieSessionFactoryConfig

from model_manager import ModelManager, WebWindMover, WebPointReleaseSpill
from util import json_date_adapter, gnome_json


# TODO: Replace with Beaker.
session_factory = UnencryptedCookieSessionFactoryConfig('ibjas45u3$@#$++slkjf__22134bbb')


def main(global_config, **settings):
    """
    This function returns a Pyramid WSGI application.
    """
    settings['Model'] = ModelManager()

    settings['package_root'] = os.path.abspath(os.path.dirname(__file__))
    settings['project_root'] = os.path.dirname(settings['package_root'])
    settings['model_images_url_path'] = 'img/%s' % settings['model_images_dir']
    settings['model_images_dir'] = os.path.join(
        settings['package_root'], 'static', 'img', settings['model_images_dir'])

    # Create the output directory if it does not exist.
    if not os.path.isdir(settings['model_images_dir']):
        os.mkdir(settings['model_images_dir'])


    # A map of :mod:`gnome` objects to route names, for use looking up the
    # route for an object at runtime with :func:`webgnome.util.get_form_route`.
    settings['form_routes'] = {
        WebWindMover: {
            'create': 'create_wind_mover',
            'update': 'update_wind_mover',
            'delete': 'delete_mover'
        },
         WebPointReleaseSpill: {
            'create': 'create_point_release_spill',
            'update': 'update_point_release_spill',
            'delete': 'delete_spill'
        },
    }

    config = Configurator(settings=settings, session_factory=session_factory)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.add_renderer('gnome_json', gnome_json)

    config.add_route('show_model', '/')
    config.add_route('model_forms', 'model/forms')
    config.add_route('create_model', '/model/create')
    config.add_route('get_time_steps', '/model/time_steps')
    config.add_route('get_next_step', '/model/next_step')
    config.add_route('get_tree', '/tree')
    config.add_route('run_model', '/model/run')
    config.add_route('run_model_until', '/model/run_until')
    config.add_route('model_settings', '/model/settings')
    config.add_route('model_map', '/model/map')
    config.add_route('create_mover', '/model/mover')
    config.add_route('delete_mover', '/model/mover/delete')
    config.add_route('create_wind_mover', '/model/mover/wind')
    config.add_route('update_wind_mover', '/model/mover/wind/{id}')
    config.add_route('create_spill', '/model/spill')
    config.add_route('delete_spill', '/model/spill/delete')
    config.add_route('create_point_release_spill', '/model/spill/point_release')
    config.add_route('update_point_release_spill', '/model/spill/point_release/{id}')

    config.scan()
    return config.make_wsgi_app()
