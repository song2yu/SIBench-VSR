export LMUData=/your/path/to/dataset/Spatial_Intelligence_Benchmark/data 

python run.py --data relative_distance Reach_Prediction Object_Shape Height Existence \
                Spatial_Compatibility Coordinate_Conversion Counting Route_Planning Trajectory_Description \
                Geometric_Reasoning Spatial_Imagination Object_Size_Estimation Spatial_Grid \
                Situational_QA Velocity_Acceleration Maze_Navigation Temporal-Appearance_Order Camera_Pose Occlusion \
                multi-view_reasoning Object_Localization Spatial_Relation --model InternVL2_5-2B --verbose --reuse
