# Copyright (c) 2019 fortiss GmbH
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT




from modules.runtime.scenario.scenario_generation.configurable_scenario_generation import ConfigurableScenarioGeneration
from modules.runtime.commons.parameters import ParameterServer
from modules.runtime.viewer.matplotlib_viewer import MPViewer
from modules.runtime.runtime import Runtime
from modules.runtime.viewer.pygame_viewer import PygameViewer
import time
import os

scenario_param_file ="highway_merge_configurable.json" # must be within examples params folder
param_server = ParameterServer(filename= os.path.join("examples/params/",scenario_param_file))
scenario_generation = ConfigurableScenarioGeneration(num_scenarios=3, params=param_server)

viewer = MPViewer(
  params=param_server,
  x_range=[5060, 5160],
  y_range=[5070,5150],
  use_world_bounds=True)
sim_step_time = param_server["simulation"]["step_time",
                                           "Step-time used in simulation",
                                           0.2]
sim_real_time_factor = param_server["simulation"]["real_time_factor",
                                                  "execution in real-time or faster",
                                                  1]

env = Runtime(0.2,
              viewer,
              scenario_generation,
              render=True)
env.reset()
for _ in range(0, 5):
  env.step()
