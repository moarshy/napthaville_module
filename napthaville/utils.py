import json
import datetime


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime.datetime):
            return obj.isoformat()
        return super().default(obj)


def scratch_to_dict(scratch):
    print(scratch)
    scratch_dict = {
        "vision_r": scratch.vision_r,
        "att_bandwidth": scratch.att_bandwidth,
        "retention": scratch.retention,
        "curr_time": scratch.curr_time.isoformat() if scratch.curr_time else None,
        "curr_tile": scratch.curr_tile,
        "daily_plan_req": scratch.daily_plan_req,
        "name": scratch.name,
        "first_name": scratch.first_name,
        "last_name": scratch.last_name,
        "age": scratch.age,
        "innate": scratch.innate,
        "learned": scratch.learned,
        "currently": scratch.currently,
        "lifestyle": scratch.lifestyle,
        "living_area": scratch.living_area,
        "concept_forget": scratch.concept_forget,
        "daily_reflection_time": scratch.daily_reflection_time,
        "daily_reflection_size": scratch.daily_reflection_size,
        "overlap_reflect_th": scratch.overlap_reflect_th,
        "kw_strg_event_reflect_th": scratch.kw_strg_event_reflect_th,
        "kw_strg_thought_reflect_th": scratch.kw_strg_thought_reflect_th,
        "recency_w": scratch.recency_w,
        "relevance_w": scratch.relevance_w,
        "importance_w": scratch.importance_w,
        "recency_decay": scratch.recency_decay,
        "importance_trigger_max": scratch.importance_trigger_max,
        "importance_trigger_curr": scratch.importance_trigger_curr,
        "importance_ele_n": scratch.importance_ele_n,
        "thought_count": scratch.thought_count,
        "daily_req": scratch.daily_req,
        "f_daily_schedule": scratch.f_daily_schedule,
        "f_daily_schedule_hourly_org": scratch.f_daily_schedule_hourly_org,
        "act_address": scratch.act_address,
        "act_start_time": scratch.act_start_time.isoformat()
        if scratch.act_start_time
        else None,
        "act_duration": scratch.act_duration,
        "act_description": scratch.act_description,
        "act_pronunciatio": scratch.act_pronunciatio,
        "act_event": list(scratch.act_event),
        "act_obj_description": scratch.act_obj_description,
        "act_obj_pronunciatio": scratch.act_obj_pronunciatio,
        "act_obj_event": list(scratch.act_obj_event),
        "chatting_with": scratch.chatting_with,
        "chat": scratch.chat,
        "chatting_with_buffer": scratch.chatting_with_buffer,
        "chatting_end_time": scratch.chatting_end_time.isoformat()
        if scratch.chatting_end_time
        else None,
        "act_path_set": scratch.act_path_set,
        "planned_path": scratch.planned_path,
    }
    return scratch_dict


def dict_to_scratch(scratch_dict):
    restored_dict = scratch_dict.copy()

    # Convert datetime strings back to datetime objects
    datetime_fields = ["curr_time", "act_start_time", "chatting_end_time"]
    for field in datetime_fields:
        if field in restored_dict and isinstance(restored_dict[field], str):
            try:
                restored_dict[field] = datetime.datetime.fromisoformat(
                    restored_dict[field]
                )
            except ValueError:
                print(
                    f"Warning: Could not convert {field} to datetime. Keeping original value."
                )

    # Convert lists back to tuples for event attributes
    tuple_fields = ["act_event", "act_obj_event"]
    for field in tuple_fields:
        if field in restored_dict and isinstance(restored_dict[field], list):
            restored_dict[field] = tuple(restored_dict[field])

    return restored_dict
