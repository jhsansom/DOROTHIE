#!/usr/bin/python3

# ==============================================================================
# -- COPYRIGHT -----------------------------------------------------------------
# ==============================================================================

# Copyright (c) 2022 SLED Lab, EECS, University of Michigan.
# authors: Martin Ziqiao Ma (marstin@umich.edu),
#          Cristian-Paul Bara (cpbara@umich.edu),
#          Owen Yidong Huang (owenhji@umich.edu),
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


from argparse import Namespace
import torch
from torch import nn
from nn.vision_encoder import VisionEncoder
from torch.nn import functional as F
from ontology.agent import PhysicalAction, PA_ARGS, DialogueMove, DialogueSlot
from nn.knowledge_encoder import RoadEncoder, JunctionEncoder, OpenDriveEncoder, LandmarkEncoder
from ontology.geometry import Lane, Landmark
from nn.graph_encoder import MapEncoder
from nn.knowledge_encoder import RoadEncoder, JunctionEncoder, OpenDriveEncoder, LandmarkEncoder
from model.util import PosEncoding

class TOTO(nn.Module):

    def __init__(self, args: Namespace):
        super(TOTO, self).__init__()
        self.args = args
        self.frame_buffer_size = 100
        self.frame_buffer_step = 4
        # self.vision_encoder = VisionEncoder(args)
        self.max_length=400
        self.temporal_embeding_dim = 770

        self.rgb_embedding_dim = 1000
        self.dlg_embedding_dim = 768 + 2 
        self.obj_embeding_dim_in = 100*256
        self.obj_def_detr_embeding_dim_in = 300*256
        self.obj_embeding_dim = 770
        self.speech_embedding_dim = 1024

        self.max_num_nodes = 486
        self.max_num_roads = 259
        self.max_num_junctions = 33
        self.max_num_streets = 14
        self.max_num_landmarks = 10
        self.map_emb_in_dim=486*64
        self.landmark_in_dim=768+57
        self.street_in_dim=768+64
        self.traj_dim=54
        
        self.belief_emb_dim = 6


        self.lane_embedding_dim = 64
        self.landmark_embedding_dim = 57
        self.id_embedding_dim = (self.lane_embedding_dim - len(Lane()) + 2)//2  # 25

        # self.temporal_embedding_dim_in = 2+1000+768+2+100*256+1024+1024
        self.temporal_embedding_dim_in = 2+self.rgb_embedding_dim
        self.temporal_embedding_dim_in += self.speech_embedding_dim
        self.temporal_embedding_dim_in += self.temporal_embeding_dim
        # self.temporal_embedding_dim_in += self.obj_embeding_dim_lin
        self.temporal_embedding_dim_in += self.belief_emb_dim

        self.temporal_embedding_dim = 1024#512#
        self.action_embedding_dim = 769
        self.action_embedding_trs_dim = self.action_embedding_dim+3

        self.frame_embedding_size = self.rgb_embedding_dim+self.dlg_embedding_dim+self.obj_embeding_dim+self.speech_embedding_dim

        # self.output_head_embedding_dim = self.frame_embedding_size




        self.action_encoder = nn.Embedding(len(PhysicalAction.__members__), self.action_embedding_dim)#args.train['d_emb'] - 1)

        self.obj_def_detr_layer = nn.Sequential(
                nn.Flatten(),
                nn.Linear(self.obj_def_detr_embeding_dim_in,self.temporal_embeding_dim),
                # nn.Dropout(0.5),
                nn.GELU(),
            )
        if self.args.ablation==6:
            self.window_emb_dim=self.traj_dim
        elif self.args.ablation==7:
            self.window_emb_dim=self.rgb_embedding_dim
        else:
            self.window_emb_dim=self.rgb_embedding_dim+self.traj_dim
        self.window_emb_layer = nn.Sequential(
                nn.Linear(self.window_emb_dim,self.temporal_embeding_dim),
                # nn.Dropout(0.5),
                nn.GELU(),
            )
        self.speech_layer = nn.Sequential(
                nn.Linear(self.speech_embedding_dim,self.temporal_embeding_dim),
                # nn.Dropout(0.5),
                nn.GELU(),
            )

        self.encoder_heads=11

        self.encoder_dropout=0.1

        self.encoder_layers=2

        encoder_layer = nn.TransformerEncoderLayer(
            self.temporal_embeding_dim, self.encoder_heads, self.temporal_embeding_dim,
            self.encoder_dropout)
        self.enc_transformer = nn.TransformerEncoder(
            encoder_layer, self.encoder_layers)


        self.enc_layernorm = nn.LayerNorm(self.temporal_embeding_dim)

        self.PosEncoding=PosEncoding()
        self.dialogue_type_input_emb_dim = 694
        self.dialogue_move_emb_dim = 64


        self.output_head_embedding_dim = self.temporal_embeding_dim = 770

        self.dlg_move_type_encoder = nn.Embedding(len(DialogueMove.__members__), self.dialogue_type_input_emb_dim)

        self.belief_output_dim = 5
        self.physical_type_output_dim = 7
        self.physical_angle_output_dim = 1
        self.dialogue_type_output_dim = 5
        self.dialogue_slot_output_dim = 69
        self.dialogue_move_output_dim = 16

        self.belief_head = nn.Sequential(
                nn.Linear(self.output_head_embedding_dim,self.belief_output_dim),
                # nn.Dropout(0.5),
                # nn.GELU(),
            )

        self.physical_type_head = nn.Sequential(
                nn.Linear(self.output_head_embedding_dim,self.physical_type_output_dim),
            )

        self.physical_angle_head = nn.Sequential(
                nn.Linear(self.output_head_embedding_dim,self.physical_angle_output_dim),
                # nn.Dropout(0.5),
                nn.Tanh(),
            )
        self.dorothy_dialogue_move_head = nn.Sequential(
                nn.Linear(self.output_head_embedding_dim,self.dialogue_move_output_dim),
            )


        self.dorothy_dialogue_type_head = nn.Sequential(
                nn.Linear(self.output_head_embedding_dim,self.dialogue_type_output_dim),
            )

        self.dorothy_dialogue_slot_head = nn.Sequential(
                nn.Linear(self.output_head_embedding_dim,self.dialogue_slot_output_dim),
            )

        self.wizzard_dialogue_move_head = nn.Sequential(
                nn.Linear(self.output_head_embedding_dim,self.dialogue_move_output_dim),
            )
        self.wizzard_dialogue_type_head = nn.Sequential(
                nn.Linear(self.output_head_embedding_dim,self.dialogue_type_output_dim),
            )

        self.wizzard_dialogue_slot_head = nn.Sequential(
                nn.Linear(self.output_head_embedding_dim,self.dialogue_slot_output_dim),
            )
    def encode_knowledge(self, lanes, edge_index, known_landmarks,landmark_names, street_ids,street_name_emb):
        map_emb = self.map_encoder.forward(lanes, edge_index, device=edge_index.device)
        landmark_emb = self.landmark_encoder.forward(known_landmarks, device=edge_index.device)
        street_emb = torch.zeros((len(street_ids), self.lane_embedding_dim)).to(edge_index.device)  # [num_streets, lane_embedding_dim]
        for i, street_id in enumerate(street_ids):
            street_emb[i] = map_emb[street_id].mean(dim=0)
        landmark_emb = torch.cat([landmark_emb,landmark_names],dim=1)
        # print(street_emb.shape,street_name_emb.shape)
        street_emb = torch.cat([street_emb,street_name_emb],dim=1)
        landmark_emb = self.landmark_emb_layer(landmark_emb)
        street_emb = self.street_emb_layer(street_emb)
        map_emb = self.map_emb_layer(map_emb.unsqueeze(0))
        # print(street_emb.shape,landmark_emb.shape,street_emb.shape)
        retval=torch.cat([map_emb,landmark_emb,street_emb],dim=0)
        return retval




    # def forward(self, dlg_emb, dlg_move_emb, act_emb, knowledge_emb, rgb, obj_detr, obj_def_detr, speech, belief_emb, sincos):
    def forward(self,  obj_def_detr,rgb_emb,knowledge_emb,speech_emb,dlg_history,dlg_move_history,act_history,belief_emb,belief_road,belief_junc,event):
        # rgb_shape = rgb.shape
        # rgb = rgb.reshape(rgb_shape[0]*rgb_shape[1],rgb_shape[2],rgb_shape[3],rgb_shape[4])
        # rgb = self.vision_encoder(rgb.permute(0,3,1,2)).reshape(rgb_shape[0],rgb_shape[1],-1)
        # rgb = torch.cat([sincos, rgb], axis=-1)
        # rgb = self.rgb_attn(rgb, rgb, rgb)[0][-1]
        # obj = torch.cat([sincos, obj], axis=-1)#.reshape(obj.shape[0],1,-1)
        # obj = self.obj_attn(obj, obj, obj)[0][-1]
        # speech = torch.cat([sincos, speech], axis=-1)#.reshape(speech.shape[0],1,-1)
        # speech = self.speech_attn(speech, speech, speech)[0][-1]
        # frame_emb = torch.cat([dlg_emb, rgb, obj, speech], axis=-1)

        # print(sincos.shape, rgb.shape, obj_def_detr.shape, speech.shape, belief_emb.shape, flush=True)

        obj_def_detr=self.obj_def_detr_layer (obj_def_detr)


        belief_opendrive=self.id_encoder(belief_road,belief_junc,device=self.args.device)
        # print(belief_emb.shape,belief_opendrive.shape,obj_def_detr.shape)
        if self.args.ablation==6:
            window_emb=torch.cat([belief_emb,belief_opendrive],dim=1)
            window_emb=self.window_emb_layer(window_emb)
            speech_emb=self.speech_layer(speech_emb.unsqueeze(0))
        elif self.args.ablation==7:
            window_emb=rgb_emb
            window_emb=self.window_emb_layer(window_emb)
            speech_emb=self.speech_layer(speech_emb.unsqueeze(0))
        else:
            window_emb=torch.cat([belief_emb,belief_opendrive,rgb_emb],dim=1)
            window_emb=self.window_emb_layer(window_emb)
            speech_emb=self.speech_layer(speech_emb.unsqueeze(0))

        # print(dlg_history.shape,dlg_move_history.shape)
        window_emb=self.PosEncoding(window_emb,event["rgb_idx"])
        act_emb=self.PosEncoding(act_history,event["act_history_idx"])
        dlg_emb=self.PosEncoding(dlg_history,event["dialog_history_idx"])
        dlg_move_emb=self.PosEncoding(dlg_move_history,event["dialog_move_idx"])
        speech_emb=self.PosEncoding(speech_emb,[event["frame"]])
        knowledge_emb=self.PosEncoding(knowledge_emb,[0])
        if self.args.ablation==2:
            emb_all=torch.cat([knowledge_emb,dlg_emb,window_emb,speech_emb,obj_def_detr],dim=0)
        elif self.args.ablation==3:
            emb_all=torch.cat([knowledge_emb,act_emb,dlg_move_emb,window_emb,speech_emb,obj_def_detr],dim=0)
        elif self.args.ablation==4:
            emb_all=torch.cat([knowledge_emb,act_emb,dlg_emb,dlg_move_emb,window_emb,obj_def_detr],dim=0)
        elif self.args.ablation==5:
            emb_all=torch.cat([knowledge_emb,act_emb,dlg_emb,dlg_move_emb,window_emb,speech_emb],dim=0)
        elif self.args.ablation==6:
            emb_all=torch.cat([knowledge_emb,act_emb,dlg_emb,dlg_move_emb,window_emb,speech_emb],dim=0)
        elif self.args.ablation==7:
            emb_all=torch.cat([act_emb,dlg_emb,dlg_move_emb,window_emb,speech_emb,obj_def_detr],dim=0)
        
        else:
            emb_all=torch.cat([knowledge_emb,act_emb,dlg_emb,dlg_move_emb,window_emb,speech_emb,obj_def_detr],dim=0)
        # emb_all=torch.cat([dlg_emb],dim=0)
        emb_all=self.enc_layernorm(emb_all)
        # print(emb_all.shape)
        enc_out=self.enc_transformer(emb_all)
        # print(enc_out.shape)
        if enc_out.shape[0]==0:
            frame_emb=torch.zeros([1,770]).to(self.args.device, non_blocking=True).float()
        else:
            frame_emb=enc_out[[-1],:]

        retval = (
            self.belief_head(frame_emb),
            self.physical_type_head(frame_emb),
            180*self.physical_angle_head(frame_emb),
            self.dorothy_dialogue_move_head(frame_emb),
            self.dorothy_dialogue_type_head(frame_emb),
            self.dorothy_dialogue_slot_head(frame_emb),
            self.wizzard_dialogue_move_head(frame_emb),
            self.wizzard_dialogue_type_head(frame_emb),
            self.wizzard_dialogue_slot_head(frame_emb)
        )

        return retval

        pass