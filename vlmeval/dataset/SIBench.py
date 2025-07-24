from .image_base import ImageBaseDataset
from .image_mcq import ImageMCQDataset
from .video_base import VideoBaseDataset
from ..smp import *
import os
import decord

class SIBench(ImageMCQDataset, ImageBaseDataset, VideoBaseDataset):
    MODALITY = 'MixedInput'
    TYPE = 'MixedOutput'

    NEED_EXTRA_PROMPT_SOURCE = ['vstibench', 'MMSI-Bench', '3DSRBench', 'OmniSpatial', 'Spatial-MM', 'SpatialMQA',
                         'VSI-Bench', 'STI-Bench', 'SpatialEval', 'SITE-Bench', 'SPHERE-VLM', 'SRBench', 'BLINK'
                         ]
    # do not need = SpatialBench, SPAR-Bench, Super-CLEVR-3D, Omni3D-Bench
    SETTING = ['Relative_Distance', 'Reach_Prediction', 'Object_Shape', 'Height', 'Existence', 'Spatial_Compatibility',
               'Coordinate_Conversion', 'Counting', 'Route_Planning', 'Trajectory_Description', 'Geometric_Reasoning',
               'Spatial_Imagination', 'Object_Size_Estimation', 'Spatial_Grid', 'Situational_QA', 'Velocity_Acceleration',
               'Maze_Navigation', 'Temporal-Appearance_Order', 'Camera_Pose', 'Occlusion', 'Multi-view_Reasoning',
               'Object_Localization'
               ]
    VIDEO_MODALITY_INCLUDED_SETTING = ['']

    FRAMES_TMPL_SYS = """
You will receive {} distinct frames that have been uniformly sampled from a video sequence, arranged in the same temporal order as they appear in the video.
Please analyze these frames and answer the question based on your observations.
"""
    FRAMES_TMPL_SYS_4VIDEO_LLM = """
You will receive several distinct frames that have been uniformly sampled from a video sequence, arranged in the same temporal order as they appear in the video.
Please analyze these frames and answer the question based on your observations.
"""
    
    def __init__(self, dataset='MMBench', skip_noimg=True, data_base='', nframe=16, fps=0):
        super(SIBench, self).__init__(dataset, skip_noimg)
        self.data_base = data_base
        self.frame_root = data_base
        self.frame_tmpl = 'frame-{}-of-{}.jpg'
        self.frame_tmpl_fps = 'frame-{}-of-{}-{}fps.jpg'

        self.nframe = nframe
        self.fps = fps
        if self.fps > 0 and self.nframe > 0:
            raise ValueError('fps and nframe should not be set at the same time')
        if self.fps <= 0 and self.nframe <= 0:
            raise ValueError('fps and nframe should be set at least one valid value')

    @classmethod
    def supported_datasets(cls):
        return ['Maze_Navigation', 'Object_Shape', 'Route_Planning']
    
    def add_extra_prompt(self, prompt, answer_type, data_source):
        if data_source in self.NEED_EXTRA_PROMPT_SOURCE:
            if answer_type == 'MCQ':
                prompt += "\nSelect from the given options, answer with letters only."
            elif answer_type == 'YN':
                prompt += "\nAnswer with 'Yes' or 'No' only."
            elif answer_type == 'Number':
                prompt += "\nAnswer using a single number and nothing else."
            else:
                raise NotImplementedError(f"Answer type '{answer_type}' is not supported. Supported types are: 'MCQ', 'YN', 'Number'.")
        elif data_source is None:
            raise KeyError("Required key 'data_source' is missing.")
        return prompt

    def frame_paths(self, video):
        # need self.frame_root & self.frame_tmpl & self.nframe
        frame_root = osp.join(self.frame_root, video)
        os.makedirs(frame_root, exist_ok=True)
        return [osp.join(frame_root, self.frame_tmpl.format(i, self.nframe)) for i in range(1, self.nframe + 1)]

    def save_video_frames(self, line):
        # need self.nframe & self.fps
        video = line['video']
        vid_path = os.path.normpath(os.path.join(self.data_base, line['video_path']))
        vid = decord.VideoReader(vid_path)
        video_info = {
            'fps': vid.get_avg_fps(),
            'n_frames': len(vid),
        }
        if self.nframe > 0 and self.fps < 0:
            step_size = len(vid) / (self.nframe + 1)
            indices = [int(i * step_size) for i in range(1, self.nframe + 1)]
            frame_paths = self.frame_paths(video)
        elif self.fps > 0:
            # not constrained by num_frames, get frames by fps
            total_duration = video_info['n_frames'] / video_info['fps']
            required_frames = int(total_duration * self.fps)
            step_size = video_info['fps'] / self.fps
            indices = [int(i * step_size) for i in range(required_frames)]
            frame_paths = self.frame_paths_fps(video, len(indices))

        flag = np.all([osp.exists(p) for p in frame_paths])

        if not flag:
            images = [vid[i].asnumpy() for i in indices]
            images = [Image.fromarray(arr) for arr in images]
            for im, pth in zip(images, frame_paths):
                if not osp.exists(pth):
                    im.save(pth)

        return frame_paths

    def save_video_into_images(self, line):
        frame_paths = self.save_video_frames(line)
        return frame_paths
    
    def build_prompt_for_video(self, line, video_llm):
        # need video_llm 
        if isinstance(line, int):
            assert line < len(self)
            line = self.data.iloc[line]

        video_path = os.path.normpath(os.path.join(self.data_base, line['video_path']))
        prompt = line['question']
        answer_type = line.get('type')
        data_source = line.get('data_source')
        prompt = self.add_extra_prompt(prompt, answer_type, data_source)

        if video_llm:
            message = [dict(type='text', value=self.FRAMES_TMPL_SYS_4VIDEO_LLM)]
            message.append(dict(type='text', value=prompt))
            message.append(dict(type='video', value=video_path))
        else:
            img_frame_paths = self.save_video_into_images(line)
            message = [dict(type='text', value=self.FRAMES_TMPL_SYS.format(len(img_frame_paths)))]
            message.append(dict(type='text', value=prompt))
            for im in img_frame_paths:
                message.append(dict(type='image', value=im))
        return message

    def build_prompt_for_image(self, line):
        msgs = []
        if line.get('image_path'):
            tgt_path = toliststr(''.join(line['image_path'].split()).split(','))
            for _ in range(len(tgt_path)):
                tgt_path[_] = os.path.join(self.data_base, tgt_path[_])
        else:
            raise KeyError("Required key 'image_path' is missing.")

        if isinstance(tgt_path, list):
            msgs.extend([dict(type='image', value=p) for p in tgt_path])
        else:
            msgs = [dict(type='image', value=tgt_path)]
        
        question = line['question']
        prompt = question
        answer_type = line.get('type')
        data_source = line.get('data_source')
        prompt = self.add_extra_prompt(prompt, answer_type, data_source)
        msgs.append(dict(type='text', value=prompt))
        return msgs

    def build_prompt(self, line, video_llm=None):
        if isinstance(line, int):
            line = self.data.iloc[line]
        
        if line.get('input_type') in ['image', 'multi-view']:
            return self.build_prompt_for_image(line=line)
        elif line.get('input_type') == 'video':
            return self.build_prompt_for_video(line=line, video_llm=video_llm)
        else:
            raise NotImplementedError(f"Unrecognized input type: {line.get('input_type')}.\
                                       Just support 'image', 'multi-view' and 'video'.")

    def evaluate(self, eval_file, **judge_kwargs):
        from .utils.multiple_choice import extract_characters_regex, report_acc
        from .utils.yorn import YOrN_Extraction
        assert eval_file.endswith('.xlsx'), 'data file should be an xlsx file'
        FAIL_MSG = 'Failed to obtain answer via API.'
        tmp_file = eval_file.replace('.xlsx', '_tmp.pkl')
        # tgt_file = eval_file.replace('.xlsx', '_rating.json')
        score_file = eval_file.replace('.xlsx', '_score.xlsx')
        score_file_csv = eval_file.replace('.xlsx', '_score.csv')

        if not osp.exists(score_file):

            res = {} if not osp.exists(tmp_file) else load(tmp_file)
            res = {k: v for k, v in res.items() if FAIL_MSG not in v}

            data = load(eval_file)
            cnt_rejected = 0
            data_un = data[~pd.isna(data['prediction'])]

            for idx in data['index']:
                ans = data.loc[data['index'] == idx, 'answer'].values[0]
                pred = data.loc[data['index'] == idx, 'prediction'].values[0]
                output_type = data.loc[data['index'] == idx, 'type'].values[0]

                if output_type == 'MCQ':
                    extract_pred = extract_characters_regex(pred)
                    if extract_pred == '':
                        cnt_rejected += 1
                        data.loc[data['index'] == idx, 'hit'] = 0
                    else:
                        data.loc[data['index'] == idx, 'hit'] = int(extract_pred == ans)
                elif output_type == 'YN':
                    extract_pred = YOrN_Extraction(pred)
                    if extract_pred == 'Unknown':
                        cnt_rejected += 1
                        data.loc[data['index'] == idx, 'hit'] = 0
                    else:
                        data.loc[data['index'] == idx, 'hit'] = int(extract_pred == ans)
                elif output_type == 'Number':
                    raise NotImplementedError

            print(
                f'Among {len(data)} questions, failed to obtain prediction for {len(data) - len(data_un)} questions, '
                f'failed to obtain the score for another {cnt_rejected} questions. '
                f'Those questions will be counted as 0 score in ALL rating.'
            )

            dump(data, score_file)
        data = load(score_file)
        acc = report_acc(data)
        dump(acc, score_file_csv)
        return acc