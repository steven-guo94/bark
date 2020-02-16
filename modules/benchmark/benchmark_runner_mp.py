# Copyright (c) 2019 fortiss GmbH
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import pickle 
import ray
import logging
import psutil
import inspect

import bark.world.evaluation
logging.getLogger().setLevel(logging.INFO)

from modules.benchmark.benchmark_runner import BenchmarkRunner, BenchmarkResult, BenchmarkConfig

# implement a parallelized version of benchmark running based on ray

# custom serialization as cloudpickling fails
def serialize_benchmark_config(bc):
  return pickle.dumps(bc)

def deserialize_benchmark_config(bc):
  return pickle.loads(bc)


# actor class running on a single core
@ray.remote
class _BenchmarkRunnerActor(BenchmarkRunner):
  def __init__(self, evaluators, terminal_when, benchmark_configs):
        super().__init__(evaluators=evaluators, 
                          terminal_when=terminal_when,
                          benchmark_configs=benchmark_configs)

# runner spawning actors and distributing benchmark configs
class BenchmarkRunnerMP(BenchmarkRunner):
    def __init__(self, benchmark_database=None,
               evaluators=None,
               terminal_when=None,
               behaviors=None,
               num_scenarios=None,
               benchmark_configs=None, num_cpus=None):
        super().__init__(benchmark_database=benchmark_database,
                          evaluators=evaluators, terminal_when=terminal_when,
                          behaviors=behaviors, num_scenarios=num_scenarios,
                          benchmark_configs=benchmark_configs,
                          )
        num_cpus_available = psutil.cpu_count(logical=True)
        if num_cpus and num_cpus <= num_cpus_available:
            pass
        else:
            num_cpus = num_cpus_available
        ray.init(num_cpus=num_cpus)
        ray.register_custom_serializer(
          BenchmarkConfig, serializer=serialize_benchmark_config,
          deserializer=deserialize_benchmark_config)
        ray.register_custom_serializer(
          BenchmarkConfig, serializer=serialize_benchmark_config,
          deserializer=deserialize_benchmark_config)
        self.benchmark_config_split = [self.benchmark_configs[i::num_cpus] for i in range(0, num_cpus)]
        self.actors = [_BenchmarkRunnerActor.remote(evaluators=evaluators,
                                                    terminal_when=terminal_when,
                                                    benchmark_configs=self.benchmark_config_split[i]) for i in range(num_cpus) ]

    def run(self):
        results_tmp = ray.get([actor.run.remote() for actor in self.actors])
        result_dict = []
        benchmark_configs = []
        for result_tmp in results_tmp:
            result_dict.extend(result_tmp.get_result_dict())
            benchmark_configs.extend(result_tmp.get_benchmark_configs())
        ray.shutdown()
        return BenchmarkResult(result_dict, benchmark_configs)