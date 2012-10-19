#!/usr/bin/env python

"""
test code for the model class

not a lot to test by itself, but a start

"""
import os, shutil
from datetime import datetime, timedelta
import numpy as np
import gnome.model
import gnome.map
import gnome.simple_mover
import gnome.spill

def test_init():
    model = gnome.model.Model()
    
def test_start_time():
    model = gnome.model.Model()

    st = datetime.now()
    model.start_time = st
    assert model.start_time == st
    
    model.step()
    
    st = datetime(2012, 8, 12, 13)
    model.start_time = st
    assert model.current_time_step == -1
    assert model.start_time == st

def test_timestep():
    model = gnome.model.Model()

    ts = timedelta(hours=1)
    model.time_step = ts
    assert model.time_step == ts.total_seconds()
    
    dur = timedelta(days=3)
    model.duration = dur
    assert model._duration == dur

def test_simple_run():
    """
    pretty much all this tests is that the model will run
    """
    
    start_time = datetime(2012, 9, 15, 12, 0)
    
    model = gnome.model.Model()
    
    model.map = gnome.map.GnomeMap()
    a_mover = gnome.simple_mover.SimpleMover(velocity=(1.0, 2.0, 0.0))
    
    model.add_mover(a_mover)

    spill = gnome.spill.PointReleaseSpill(num_LEs=10,
                                          start_position = (0.0, 0.0, 0.0),
                                          release_time = start_time,
                                          )
    
    model.add_spill(spill)
    model.start_time = spill.release_time
    
    # test iterator:
    for step in model:
        print "just ran time step: %s"%model.current_time_step

    # reset and run again:
    model.reset()
    # test iterator:
    for step in model:
        print "just ran time step: %s"%model.current_time_step
        
    assert True
    
def test_simple_run_with_map():
    """
    pretty much all this tests is that the model will run
    """
    
    start_time = datetime(2012, 9, 15, 12, 0)
    
    model = gnome.model.Model()
    
    model.map = gnome.map.MapFromBNA( 'SampleData/MapBounds_Island.bna',
                                refloat_halflife=6*3600, #seconds
                                )
    a_mover = gnome.simple_mover.SimpleMover(velocity=(1.0, 2.0, 0.0))
    
    model.add_mover(a_mover)

    spill = gnome.spill.PointReleaseSpill(num_LEs=10,
                                          start_position = (0.0, 0.0, 0.0),
                                          release_time = start_time,
                                          )
    
    model.add_spill(spill)
    model.start_time = spill.release_time
    
    # test iterator:
    for step in model:
        print "just ran time step: %s"%step

    # reset and run again:
    model.reset()
    # test iterator:
    for step in model:
        print "just ran time step: %s"%step
        
    assert True

import gnome.utilities.map_canvas
from gnome.utilities.file_tools import haz_files
def test_simple_run_with_image_output():
    """
    pretty much all this tests is that the model will run and output images
    """
    
    # create a place for test images (cleaning out any old ones)
    images_dir = "Test_images"
    if os.path.isdir(images_dir):
        shutil.rmtree(images_dir)
    os.mkdir(images_dir)

    start_time = datetime(2012, 9, 15, 12, 0)
    
    model = gnome.model.Model()
    model.images_dir = images_dir
    model.duration = timedelta(hours=1)

    mapfile = "SampleData/MapBounds_Island.bna"

    # the land-water map
    model.map = gnome.map.MapFromBNA( mapfile,
                                      refloat_halflife=6*3600, #seconds
                                     )
    # the image output map
    map = gnome.utilities.map_canvas.MapCanvas((150, 100))
    polygons = haz_files.ReadBNA("SampleData/MapBounds_2Spillable2Islands2Lakes.bna", "PolygonSet")
    map.set_land(polygons)
    model.output_map = map
    
    a_mover = gnome.simple_mover.SimpleMover(velocity=(1.0, -1.0, 0.0))
    model.add_mover(a_mover)

    N = 10 # a line of ten points
    start_points = np.zeros((N, 3) , dtype=np.float64)
    start_points[:,0] = np.linspace(-127.1, -126.1, N)
    start_points[:,1] = np.linspace( 47.93, 48.05, N)
    #print start_points
    spill = gnome.spill.PointReleaseSpill(num_LEs=10,
                                          start_position = start_points,
                                          release_time = start_time,
                                          )
    
    model.add_spill(spill)
    model.start_time = spill.release_time
    #image_info = model.next_image()

    while True:
         print "calling next_image"
         try:
             image_info = model.next_image()
             print image_info
         except StopIteration:
             print "Done with the model run"
             break

    assert True
    
# if __name__ == "__main__":
#     test_simple_run_with_image_output()
    
    
    

    