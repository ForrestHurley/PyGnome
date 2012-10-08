#!/usr/bin/env python

"""
Wind_mover.py

Python wrapper around the Cython wind_mover module

"""

## make sure the main lib is imported
import gnome.cy_gnome.cy_basic_types

from gnome.cy_gnome.cy_wind_mover import CyWindMover

##fixme: should this use delegation, rather than subclassing?
class WindMover(CyWindMover):
    """
    WindMover class
    
    the real work is delegated to the cython class
    
    but this sets everything up
    """
    def __init__(self, wind_vel=):
        """
        not much here, but there should be!
        """
        Cy_wind_mover.__init__(self)
        
        # keep the cython version around
        self_get_move = Cy_wind_mover.get_move
            
    def get_move(self, spill, time_step, model_time):
        """
        moves the particles defined in the spill object
        
        :param spill: spill is an instance of the gnome.spill.Spill class
        :param time_step: time_step in seconds
        :param model_time: current model time as a datetime instance
        
        In this case, it uses the:
            positions
            status_code
        data arrays.
        
        """
        
        # Get the data:
        try:
            positions      = spill['positions']
            status_codes   = spill['status_codes']
        except KeyError, err:
            raise ValueError("The spill does not have the required data arrays\n"+err.message)
        
        model_time_seconds = basic_types.dt_to_epoch(model_time)        
        positions = position.view(dtype = basic_types.world_point)
        delta = np.zeros_like(positions)
                
        ## should we need these???
        windage_array = np.ones((spill.num_LEs,), dtype=basic_types.mover_type)

        # initialize uncertainty array:
        # fixme: this needs to get stored with the Mover -- keyed to a particular spill.
        uncertain_ra = np.empty((spill.num_LEs,), dtype=basic_types.wind_uncertain_rec)	# one uncertain rec per le
        for x in range(0, N):
            theta = random()*2*pi
            uncertain_ra[x]['randCos'] = cos(theta)
            uncertain_ra[x]['randSin'] = sin(theta)


        # call the Cython version 
        # (delta is changed in place)
        self._get_move(self,
                       model_time,
                       time_step,
                       positions,
                       delta,
                       windage_array):
        return delta

        
        
    
    
    