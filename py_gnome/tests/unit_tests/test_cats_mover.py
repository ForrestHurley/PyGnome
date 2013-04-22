'''
Test all operations for cats mover work
'''
import datetime
import os

import numpy as np
import pytest

from gnome import environment, movers, basic_types
from gnome.spill_container import TestSpillContainer
from gnome.utilities import time_utils

curr_file= os.path.join( os.path.dirname(__file__), r"SampleData/long_island_sound/tidesWAC.CUR")
td = environment.Tide(filename=os.path.join( os.path.dirname(__file__), r"SampleData/long_island_sound/CLISShio.txt"))

def test_exceptions():
    """
    Test correct exceptions are raised
    """
    bad_file=r"SampleData/long_island_sound/tidesWAC.CURX"
    with pytest.raises(ValueError):
        movers.CatsMover(bad_file)
        
    with pytest.raises(TypeError):
        movers.CatsMover(curr_file, tide=10)

num_le = 3
start_pos = (-72.5, 41.17, 0)
rel_time = datetime.datetime(2012, 8, 20, 13)
time_step = 15*60 # seconds
model_time = time_utils.sec_to_date(time_utils.date_to_sec(rel_time))

# NOTE: Following expected results were obtained from Gnome for the above test setup.
#       These are documented here, though there is no test to check against these values.
# TODO: There needs to be a simpler test for testing the values. Simple datafiles exist,
#       the test just needs to be completed. 
#
#         expected_shio_only = (-0.00089881, 0.00303475, 0.)
#         expected_cats_shio = ( 0.00020082,-0.00067807, 0.)
#
#       For now, the expected gnome results are documented here for above test.
# certain spill, expected results for this model_time and the above shio and currents file
# These were obtained from Gnome, so have been added here to explicitly test against
# If any of the above setup parameters change, these results will not match!

def test_loop():
    """
    test one time step with no uncertainty on the spill
    checks there is non-zero motion.
    also checks the motion is same for all LEs
    """
    pSpill = TestSpillContainer(num_le, start_pos, rel_time)
    cats   = movers.CatsMover(curr_file, tide=td)
    delta  = _certain_loop(pSpill, cats)
    
    _assert_move(delta)
    
    assert np.all( delta[:,0]== delta[0,0] )    # lat move is the same for all LEs
    assert np.all( delta[:,1]== delta[0,1] )    # long move is the same for all LEs
    assert np.all( delta[:,2] == 0 )            # 'z' is zeros
    
    return delta

def test_uncertain_loop():
    """
    test one time step with uncertainty on the spill
    checks there is non-zero motion.
    """
    pSpill = TestSpillContainer(num_le, start_pos, rel_time, uncertain=True) 
    cats = movers.CatsMover(curr_file, tide=td)
    u_delta = _uncertain_loop(pSpill,cats)
    
    _assert_move(u_delta)
    
    return u_delta

def test_certain_uncertain():
    """
    make sure certain and uncertain loop results in different deltas
    """
    delta  = test_loop()
    u_delta= test_uncertain_loop()
    print
    print delta
    print u_delta
    assert np.all(delta[:,:2] != u_delta[:,:2])
    assert np.all(delta[:,2] == u_delta[:,2])

c_cats = movers.CatsMover(curr_file)
def test_default_props():
    """
    test default properties
    """
    assert c_cats.scale == False
    assert c_cats.scale_value == 1
    
def test_scale():  
    """
    test setting / getting properties
    """
    c_cats.scale = True
    assert c_cats.scale == True

def test_scale_value():
    """
    test setting / getting properties
    """
    c_cats.scale_value = 0
    print c_cats.scale_value
    assert c_cats.scale_value == 0
    
def test_scale_refpoint():
    """
    test setting / getting properties
    """
    tgt = (1,2,3)
    c_cats.scale_refpoint = tgt  # can be a list or a tuple
    assert c_cats.scale_refpoint == tuple(tgt)
    c_cats.scale_refpoint = list(tgt)  # can be a list or a tuple
    assert c_cats.scale_refpoint == tuple(tgt)

# Helper functions for tests
def _assert_move(delta):
    """
    helper function to test assertions
    """
    print
    print delta
    assert np.all( delta[:,:2] != 0)
    assert np.all( delta[:,2] == 0)

def _certain_loop(pSpill, cats):
    cats.prepare_for_model_run()
    cats.prepare_for_model_step(pSpill, time_step, model_time)
    delta = cats.get_move(pSpill, time_step, model_time)
    cats.model_step_is_done()
    
    return delta

def _uncertain_loop(pSpill, cats):
    cats.prepare_for_model_run()
    cats.prepare_for_model_step(pSpill, time_step, model_time)
    u_delta = cats.get_move(pSpill, time_step, model_time)
    cats.model_step_is_done()
    
    return u_delta

def test_exception_new_from_dict():
    """
    test exceptions raised for new_from_dict
    """
    c_cats = movers.CatsMover(curr_file)
    dict_ = c_cats.to_dict('create')
    dict_.update({'tide': td})
    with pytest.raises(ValueError):
        c2 = movers.CatsMover.new_from_dict(dict_)

def test_new_from_dict_tide():
    """
    test to_dict function for Wind object
    create a new wind object and make sure it has same properties
    """
    c_cats = movers.CatsMover(curr_file, tide=td)
    dict_ = c_cats.to_dict('create')
    dict_.update({'tide':td})
    c2 = movers.CatsMover.new_from_dict(dict_)
    assert c_cats == c2
    
def test_new_from_dict_curronly():
    """
    test to_dict function for Wind object
    create a new wind object and make sure it has same properties
    """
    c_cats = movers.CatsMover(curr_file)
    dict_ = c_cats.to_dict('create')
    c2 = movers.CatsMover.new_from_dict(dict_)
    assert c_cats == c2

    