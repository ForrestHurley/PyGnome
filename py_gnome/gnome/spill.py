#!/usr/bin/env python

"""
spill.py - An implementation of the spill class(s)

A "spill" is essentially a source of elements. These classes provide
the logic about where an when the elements are released 

"""
import copy

import math
from datetime import timedelta
import numpy as np
from gnome import basic_types
from gnome import GnomeId
from gnome.utilities import serializable

class ArrayType(object):#,serializable.Serializable):
    """
    Object used to capture attributes of numpy data array for elements

    An ArrayType specifies how data arrays associated with elements
    are defined.

    Used by :class:`Spill` and :class:`gnome.spill_container.SpillContainer` 
    """
    
    def __init__(self, shape, dtype, initial_value=None):
        """
        constructor for ArrayType
        
        :param shape: shape of the numpy array
        :type shape: tuple of integers
        :param dtype: numpy datatype contained in array
        :type dtype: numpy dtype
        :param initial_value: initialize array to this value
        :type initial_value: numpy array of size: shape(:-1) (ie. the shape of a single element)
        """
        self.shape = shape
        self.dtype = dtype
        self.initial_value = initial_value

    def __eq__(self, other):
        """" Equality of two ArrayType objects """
        if not isinstance(other, self.__class__):
            return False
        
        if len(self.__dict__) != len(other.__dict__):   
            return False
        
        for key,val in self.__dict__.iteritems():
             if key not in other.__dict__:
                 return False
             
             elif val != other.__dict__[key]:
                 return False
             
        # everything passed, then they must be equal
        return True
    
    def __ne__(self,other):
        """ 
        Compare inequality (!=) of two objects
        """
        if self == other:
            return False
        else:
            return True
        
    

class Spill(object):
    """
    base class for a source of elements
    
    .. note:: This class is not serializable since it can't be used in PyGnome
    """
    positions = ArrayType( (3,), basic_types.world_point_type)
    next_positions = ArrayType( (3,), basic_types.world_point_type)
    last_water_positions = ArrayType( (3,), basic_types.world_point_type)
    status_codes = ArrayType( (), basic_types.status_code_type,
                              basic_types.oil_status.in_water)
    spill_num = ArrayType( (), basic_types.id_type)


    # Should ArrayType objects be saved? Can they be updated?
    _update = ['num_elements','on']
    _create = []
    _create.extend(_update)
    state = copy.deepcopy(serializable.Serializable.state)
    state.add( create=_create, update=_update)

    @property
    def array_types(self):
        return dict([(name, getattr(self, name))
                for name in dir(self)
                if name != 'array_types'
                and type(getattr(self, name)) == ArrayType])

    @property
    def id(self):
        return self._gnome_id.id
    
    def __init__(self, num_elements=0, on=True, id=None):
        """
        Base spill class. Spill used by a gnome model derive from this base class
        
        :param num_elements: number of LEs - default is 0.
        :type num_elements: int
        
        Optional parameters (kwargs):
        
        :param on: Toggles the spill on/off (bool). Default is 'on'.
        :type on: bool
        :param id: Unique Id identifying the newly created mover (a UUID as a string), used when loading from a persisted model
        :type id: str
        """
        self.num_elements = num_elements
        self.on = on       # sets whether the spill is active or not
        self._gnome_id = GnomeId(id)

    def __deepcopy__(self, memo=None):
        """
        the deepcopy implementation

        we need this, as we don't want the spill_nums copied, but do want everything else.

        got the method from:

        http://stackoverflow.com/questions/3253439/python-copy-how-to-inherit-the-default-copying-behaviour

        Despite what that thread says for __copy__, the built-in deepcopy() ends up using recursion
        """
        obj_copy = object.__new__(type(self))
        obj_copy.__dict__ = copy.deepcopy(self.__dict__, memo)  # recursively calls deepcopy on GnomeId object
        return obj_copy

    def __copy__(self):
        """
        Make a shallow copy of the object
        
        It makes a shallow copy of all attributes defined in __dict__
        Since it is a shallow copy of the dict, the _gnome_id object is not copied, but merely referenced
        This seems to be standard python copy behavior so leave as is. 
        """
        obj_copy = object.__new__(type(self))
        obj_copy.__dict__ = copy.copy(self.__dict__)
        return obj_copy

    def uncertain_copy(self):
        """
        Returns a deepcopy of this spill for the uncertainty runs

        The copy has everything the same, including the spill_num,
        but it is a new object with a new id.

        Not much to this method, but it could be overridden to do something
        fancier in the future or a subclass.
        """
        u_copy = copy.deepcopy(self)
        return u_copy

    def rewind(self):
        """
        rewinds the Spill to original status (before anything has been released)
        Nothing needs to be done for the base class, but this method will be
        overloaded by subclasses and defined to fit their implementation
        """
        pass

    def release_elements(self, current_time, time_step, array_types=None):
        """
        probably overridden by a subclass
        """
        return None

    def create_new_elements(self, num_elements, array_types=None):
        arrays = {}
        if not array_types:
            array_types = self.array_types

        for name, array_type in array_types.iteritems():
            #===================================================================
            # if array_type.shape == ():  # it is a scalar array
            #    arrays[name] = np.array(0,dtype=array_type.dtype)
            # else:
            #===================================================================
            arrays[name] = np.zeros( (num_elements,)+array_type.shape, dtype=array_type.dtype)
        self.initialize_new_elements(arrays, array_types)
        return arrays

    def initialize_new_elements(self, arrays, array_types=None):
        if not array_types:
            array_types = self.array_types

        for name, array_type in array_types.iteritems():
            if array_type.initial_value != None:
                arrays[name][:] = array_type.initial_value

class FloatingSpill(Spill):
    """
    Spill for floating objects

    all this does is add the 'windage' parameter
    
    NOTE: This class is not serializable since it can't be used in PyGnome
    """
    windages = ArrayType( (), basic_types.windage_type)

    _update= ['windage_range','windage_persist']
    _create= []
    _create.extend(_update) 
    state  = copy.deepcopy(Spill.state)
    state.add(update=_update, create=_create)
    
    def __init__(self,
                 windage_range=(0.01, 0.04),
                 windage_persist=900, **kwargs):
        """
        Object constructor. 
        
        Note on windage_range:
            The windage is computed by randomly sampling between this range and 
            normalizing it by windage_persist so windage is independent of model time_step.
            
        windage_persist:
            The 0 or -1 means the persistence is infinite so it is only set at the beginning of the run.
            
        Optional arguments:
        :param windage_range: A tuple defining the min/max % of wind acting on each LE. Default (0.01, 0.04)
        :type windage_range: a tuple of size 2 (min, max)
        :param windage_persist: Duration over which windage persists - this is given in seconds. Default is 900s.
        :type windage_persist: integer
        
        .. note:: Remaining kwargs are passed onto Spill's __init__ using super.  See base class documentation for remaining valid kwargs.
        """
        super(FloatingSpill, self).__init__(**kwargs)
        self.windage_range = windage_range
        self.windage_persist = windage_persist

class SurfaceReleaseSpill(FloatingSpill, serializable.Serializable):
    """
    The primary spill source class  --  a point release of floating
    non-weathering particles, can be instantaneous or continuous, and be
    released at a single point, or over a line.

    """
    _update= ['start_position','release_time','end_position','end_release_time']
    _create= ['num_released', 'not_called_yet', 'prev_release_pos','delta_pos'] # not sure these should be user update able
    _create.extend(_update)
    state  = copy.deepcopy(FloatingSpill.state)
    state.add(update=_update, create=_create)
    
    @classmethod
    def new_from_dict(cls, dict_):
        new_obj = cls(num_elements=dict_.pop('num_elements'),
                      start_position=dict_.pop('start_position'),
                      release_time=dict_.pop('release_time'),
                      end_position=dict_.pop('end_position',None),
                      end_release_time=dict_.pop('end_release_time',None),
                      windage_range=dict_.pop('windage_range'),
                      windage_persist=dict_.pop('windage_persist'),
                      id=dict_.pop('id') )
        
        for key in dict_.keys():
            setattr(new_obj, key, dict_[key])
            
        return new_obj
     
    def __init__(self,
                 num_elements,
                 start_position,
                 release_time,
                 end_position=None,
                 end_release_time=None,
                 windage_range=(0.01, 0.04),
                 windage_persist=900,
                 **kwargs):
        """
        :param num_elements: total number of elements to be released
        :type num_elements: integer

        :param start_position: initial location the elements are released
        :type start_position: 3-tuple of floats (long, lat, z)

        :param release_time: time the LEs are released (datetime object)
        :type release_time: datetime.datetime

        :param end_position=None: optional -- for a moving source, the end position
        :type end_position: 3-tuple of floats (long, lat, z)

        :param end_release_time=None: optional -- for a release over time, the end release time
        :type end_release_time: datetime.datetime

        :param windage_range=(0.01, 0.04): the windage range of the elements default is (0.01, 0.04) from 1% to 4%.
        :type windage_range: tuple: (min, max)

        :param windage_persist=-1: Default is 900s, so windage is updated every 900 sec.
                                -1 means the persistence is infinite so it is only set at the beginning of the run.
        :type windage_persist: integer seconds

        Remaining kwargs are passed onto base class __init__ using super. 
        See :class:`FloatingSpill` documentation for remaining valid kwargs.
        """
        super(SurfaceReleaseSpill, self).__init__(windage_range, windage_persist, **kwargs)
        
        self.num_elements = num_elements
        
        self.release_time = release_time
        if end_release_time is None:
            self.end_release_time = release_time    # also sets self._end_release_time
        else:
            if release_time > end_release_time:
                raise ValueError("end_release_time must be greater than release_time")
            self.end_release_time = end_release_time

        if end_position is None:
            end_position = start_position   # also sets self._end_position
        self.start_position = np.array(start_position, dtype=basic_types.world_point_type).reshape((3,))
        self.end_position = np.array(end_position, dtype=basic_types.world_point_type).reshape((3,))
        if self.num_elements == 1:
            self.delta_pos = np.array( (0.0,0.0,0.0) , dtype=basic_types.world_point_type)
        else:
            self.delta_pos = (self.end_position - self.start_position) / (self.num_elements-1)
        self.delta_release = (self.end_release_time - self.release_time).total_seconds() 
        self.start_position = np.asarray(start_position, dtype=basic_types.world_point_type).reshape((3,))
        self.end_position = np.asarray(end_position, dtype=basic_types.world_point_type).reshape((3,))
        #self.positions.initial_value = self.start_position

        #self.windage_range    = windage_range[0:2]
        #self.windage_persist  = windage_persist

        self.num_released = 0
        self.not_called_yet = True
        self.prev_release_pos = self.start_position.copy()

    """
    Following properties were added primarily for setting values correctly when json input
    form webgnome is convereted to dict which is then used by from_dict to update variables.
    In this case, if user does not set end_positions or end_release_time, they become None in the
    dict. If these are None, then they should be updated to match release_time and start_position. 
    """
    @property
    def end_position(self):
        return self._end_position
    
    @end_position.setter
    def end_position(self, val):
        if val is None:
            self._end_position = self.start_position
        else:
            self._end_position = val
            
    @property
    def end_release_time(self):
        return self._end_release_time
    
    @end_release_time.setter
    def end_release_time(self, val):
        if val is None:
            self._end_release_time = self.release_time
        else:
            self._end_release_time = val        

    def release_elements(self, current_time, time_step, array_types=None):
        """
        Release any new elements to be added to the SpillContainer

        :param current_time: current time
        :type current_time: datetime.datetime 

        :param time_step: the time step, sometimes used to decide how many should get released.
        :type time_step: integer seconds

        :returns : None if there are no new elements released. A dict of arrays if there are new elements
        """

        if not array_types:
            array_types = self.array_types

        if self.num_released >= self.num_elements:
            # nothing left to release
            return None

        if current_time > self.release_time and self.not_called_yet:
            #first call after release time -- don't release anything
            #self.not_called_yet = False
            return None
        # it's been called before the release_time
        self.not_called_yet = False

        if current_time+timedelta(seconds=time_step) <= self.release_time: # don't want to barely pick it up...
            # not there yet...
            print "not time to release yet"
            return None

        if self.delta_release <= 0:
            num = self.num_elements
            arrays = self.create_new_elements(num, array_types)
            self.num_released = num
            if np.array_equal(self.delta_pos, (0.0,0.0,0.0)):
                #point release
                arrays['positions'][:,:] = self.start_position
            else:
                arrays['positions'][:,0] = np.linspace(self.start_position[0],self.end_position[0] , num)
                arrays['positions'][:,1] = np.linspace(self.start_position[1],self.end_position[1] , num)
                arrays['positions'][:,2] = np.linspace(self.start_position[2],self.end_position[2] , num)
            return arrays

        n_0 = self.num_released # always want to start at previous released
        #index of end of current time step
        n_1 = int( ( (current_time - self.release_time).total_seconds() + time_step) /
                      self.delta_release * (self.num_elements-1) ) # a tiny bit to make it open on the right.

        n_1 = min(n_1, self.num_elements-1) # don't want to go over the end.
        if n_1 == self.num_released-1: # indexes from zero
            # none to release this time step
            return None

        num = n_1 - n_0 + 1
        self.num_released = n_1+1 # indexes from zero
        
        arrays = self.create_new_elements(num, array_types)

        #compute the position of the elements:
        if np.array_equal(self.delta_pos, (0.0,0.0,0.0) ):
            # point release
            arrays['positions'][:,:] = self.start_position
        else:
            n = np.arange(n_0, n_1+1).reshape((-1,1))
            if self.num_elements == 1: # special case this one
                pos = np.array( [self.start_position,] )
            else:
                pos = self.start_position + n*self.delta_pos
            arrays['positions'] = pos

        return arrays

    def rewind(self):
        """
        reset to initial conditions -- i.e. nothing released.
        """
        super(SurfaceReleaseSpill, self).rewind()

        self.num_released = 0
        self.not_called_yet = True
        self.prev_release_pos = self.start_position


class SubsurfaceSpill(Spill):
    """
    spill for underwater objects

    all this does is add the 'water_currents' parameter
    """
    water_currents = ArrayType( (3,), basic_types.water_current_type)

    def __init__(self):
        super(SubsurfaceSpill, self).__init__()
        # it is not clear yet (to me anyway) what we will want to add to a subsurface spill


class SubsurfaceReleaseSpill(SubsurfaceSpill):
    """
    The second simplest spill source class  --  a point release of underwater
    non-weathering particles

    .. todo::
        'gnome.cy_gnome.cy_basic_types.oil_status' does not currently have an underwater status.
        for now we will just keep the in_water status, but we will probably want to change this
        in the future.
    """
    def __init__(self,
                 num_elements,
                 start_position,
                 release_time,
                 end_position=None,
                 end_release_time=None,
                 ):
        """
        :param num_elements: total number of elements used for this spill
        :param start_position: location the LEs are released (long, lat, z) (floating point)
        :param release_time: time the LEs are released (datetime object)
        :param end_position=None: optional -- for a moving source, the end position
        :param end_release_time=None: optional -- for a release over time, the end release time
        """
        super(SubsurfaceReleaseSpill, self).__init__()

        self.num_elements = num_elements

        self.release_time = release_time
        if end_release_time is None:
            self.end_release_time = release_time
        else:
            if release_time > end_release_time:
                raise ValueError("end_release_time must be greater than release_time")
            self.end_release_time = end_release_time

        if end_position is None:
            end_position = start_position
        self.start_position = np.asarray(start_position, dtype=basic_types.world_point_type).reshape((3,))
        self.end_position = np.asarray(end_position, dtype=basic_types.world_point_type).reshape((3,))
        #self.positions.initial_value = self.start_position

        self.num_released = 0
        self.prev_release_pos = self.start_position

    def release_elements(self, current_time, time_step, array_types=None):
        """
        Release any new elements to be added to the SpillContainer

        :param current_time: datetime object for current time
        :param time_step: the time step, in seconds -- used to decide how many should get released.

        :returns : None if there are no new elements released
                   a dict of arrays if there are new elements
        """
        if not array_types:
            array_types = self.array_types

        if current_time >= self.release_time:
            if self.num_released >= self.num_elements:
                return None

            #total release time
            release_delta = (self.end_release_time - self.release_time).total_seconds()
            if release_delta == 0: #instantaneous release
                num = self.num_elements - self.num_released #num_released should always be 0?
            else:
                # time since release began
                if current_time >= self.end_release_time:
                    dt = release_delta
                else:
                    dt = max( (current_time - self.release_time).total_seconds() + time_step, 0.0)
                    total_num = (dt / release_delta) * self.num_elements
                    num = int(total_num - self.num_released)

            if num <= 0: # all released
                return None

            self.num_released += num

            arrays = self.create_new_elements(num, array_types)

            #compute the position of the elements:
            if release_delta == 0: # all released at once:
                x1, y1 = self.start_position[:2]
                x2, y2 = self.end_position[:2]
                arrays['positions'][:,0] = np.linspace(x1, x2, num)
                arrays['positions'][:,1] = np.linspace(y1, y2, num)
            else:
                x1, y1 = self.prev_release_pos[:2]
                dx = self.end_position[0] - self.start_position[0]
                dy = self.end_position[1] - self.start_position[1]

                fraction = min (1, dt / release_delta)
                x2 = (fraction * dx) + self.start_position[0]
                y2 = (fraction * dy) + self.start_position[1]
                    

                if np.array_equal(self.prev_release_pos, self.start_position):
                    # we want both the first and last points
                    arrays['positions'][:,0] = np.linspace(x1, x2, num)
                    arrays['positions'][:,1] = np.linspace(y1, y2, num)
                else:
                    # we don't want to duplicate the first point.
                    arrays['positions'][:,0] = np.linspace(x1, x2, num+1)[1:]
                    arrays['positions'][:,1] = np.linspace(y1, y2, num+1)[1:]
                self.prev_release_pos = (x2, y2, 0.0)
            return arrays
        else:
            return None

    def rewind(self):
        """
        rewind to initial conditions -- i.e. nothing released. 
        """
        super(SubsurfaceReleaseSpill, self).rewind()

        self.num_released = 0
        self.prev_release_pos = self.start_position


class SpatialReleaseSpill(FloatingSpill):
    """
    A simple spill class  --  a release of floating non-weathering particles,
    with their initial positions pre-specified

    """
    def __init__(self,
                 start_positions,
                 release_time,
                 windage_range=(0.01, 0.04),
                 windage_persist=900,
                 ):
        """
        :param start_positions: locations the LEs are released
        :type start_positions: (num_elements, 3) numpy array of float64 -- (long, lat, z)

        :param release_time: time the LEs are released
        :type release_time: datetime.datetime

        :param windage=(0.01, 0.04): the windage range of the LEs  Default is from 1% to 4%.
        :param windage: tuple of floats: (min, max). 

        :param persist=900: Default is 900s, so windage is updated every 900 sec. The -1 means the persistence is infinite so it is only set at the beginning of the run.
        :type persist: integer secondsDefault 
                        The -1 means the persistence is infinite so it is only set at the beginning of the run.
        """
        super(SpatialReleaseSpill, self).__init__(windage_range, windage_persist)
        
        self.start_positions = np.asarray(start_positions,
                                          dtype=basic_types.world_point_type).reshape((-1, 3))
        self.num_elements = self.start_positions.shape[0]

        self.release_time = release_time

        self.elements_not_released = True
        self.not_called_yet = True
        self.windage_range    = windage_range[0:2]
        self.windage_persist  = windage_persist

    def release_elements(self, current_time, time_step, array_types=None):
        """
        Release any new elements to be added to the SpillContainer

        :param current_time: current time
        :type current_time: datetime.datetime 

        :param time_step: the time step, sometimes used to decide how many should get released.
        :type time_step: integer seconds

        :returns : None if there are no new elements released. A dict of arrays if there are new elements

        .. note:: this releases all the elements at their initial positions at the release_time
        """
        if not array_types:
            array_types = self.array_types

        if current_time > self.release_time and self.not_called_yet:
            #first call after release time -- don't release anything
            return None
        # it's been called before the release_time
        self.not_called_yet = False

        if self.elements_not_released and current_time >= self.release_time:
            self.elements_not_released = False
            arrays = self.create_new_elements(self.num_elements, array_types)
            arrays['positions'][:,:] = self.start_positions
            return arrays
        else:
            return None

    def rewind(self):
        """
        rewind to initial conditions -- i.e. nothing released. 
        """
        self.elements_not_released = True
        self.not_called_yet = True
