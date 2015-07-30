import notmuch
from notmuch.message import Message
from notmuch.messages import Messages
from notmuch.thread import Thread
from django.conf import settings

import time, email, datetime

def to_str (func) :
    return lambda x : str (func (x))
def to_str_arr (func) :
    return lambda x : [str (y) for y in func (x)]
def to_str_split (func, sep) :
    return lambda x : str (func (x)).split (sep)

def part_details (part, count = 0, details = {}) :
    valid_details  = {'id' : lambda p : {'type' : "filename", 'value' : p.get_filename()} if p.get_filename() != None else {'type' : "count", 'value' : count},
                      'charset': lambda p : p.get_content_charset ("utf8"),
                      'maintype' :  email.message.Message.get_content_maintype ,
                      'subtype' :  email.message.Message.get_content_subtype,
                      'disposition' : lambda p : str (p ['Content-Disposition']).split (";")[0],
    }

    result = {}
    for key in details :
        if key in valid_details :
            result [key] = valid_details [key] (part)
    return result

def get_parts_details (message, details) :
    count = 0
    parts = []

    fp = open(message.get_filename(), encoding='utf-8', errors='replace')
    email_msg = email.message_from_file(fp)
    fp.close()

    if email_msg.is_multipart () == False :
        parts.append (part_details (email_msg, 0, details))
    else :
        _count = 0
        for email_part in email_msg.walk () :
            parts.append (part_details (email_part, _count, details))
            _count += 1

    return parts

def manage (search) :
    result = { 'ok' : False }
    database_path = settings.NOTMUCH_DB
    exclude_tags = settings.EXCLUDE_TAGS

    database = notmuch.Database(database_path)
    query = notmuch.Query (database, search ['reference'] if "reference" in search else "")
    for tag in exclude_tags :
        query.exclude_tag (tag)

    if not "type" in search or search ['type'] == "message" :
        search_function = query.search_messages
        valid_global  = {'tags' : to_str_arr (Messages.collect_tags)}
        valid_details = {'id' : to_str (Message.get_message_id),
                         'thread_id' : to_str (Message.get_thread_id),
                         'tags' : to_str_arr (Message.get_tags),
                         'author': lambda msg : Message.get_header (msg, "From"),
                         'subject' : lambda msg : Message.get_header (msg, "Subject"),
                         'to': lambda msg : Message.get_header (msg, "To").split (","),
                         'cc': lambda msg : Message.get_header (msg, "Cc").split (","),
                         'bcc': lambda msg : Message.get_header (msg, "Bcc").split (","),
                         'date': lambda msg : time.strftime("%d %b, %X", time.localtime(msg.get_date())),
                         'parts' : lambda msg : get_parts_details (msg, search ['parts_details'] if 'parts_details' in search else {}),
        }
    elif search ['type'] == "thread" :
        search_function = query.search_threads
        valid_global  = {}
        valid_details = {'id' : to_str (Thread.get_thread_id),
                         'authors' : to_str_split (Thread.get_authors, ","),
                         'subject' : to_str (Thread.get_subject),
                         'dates' : lambda thread : [time.strftime("%d %b, %X", time.localtime (thread.get_oldest_date())), time.strftime("%d %b, %X", time.localtime (thread.get_newest_date()))],
                         'tags' : to_str_arr (Thread.get_tags),
                         'count' : Thread.get_total_messages,
                         'messages_id' : lambda Thread : [str (msg.get_message_id ()) for msg in Thread.get_messages ()],
                         # 'toplevel_messages_id' : lambda thread : [str (msg.get_message_id ()) for msg in thread.get_toplevel_messages ()]
        }

    if 'global' in search :
        global_elements = search_function ()
        result ['global'] = {}
        for key in search ['global'] :
            if key in valid_global :
                result ['global'][key] = valid_global [key] (global_elements)
        del (global_elements)

    if 'details' in search :
        elements = search_function ()
        if 'options' in search and 'max_count' in search ['options'] :
            max_count_present = True
            max_count = search ['options']['max_count']
        else :
            max_count_present = False
        if 'options' in search and 'max_delay' in search ['options']:
            max_delay_present = True
            max_delay = search ['options']['max_delay']
        else :
            max_delay_present = False

        _count = 0
        _t0 = datetime.datetime.now ()
        for elt in elements :
            result [_count] = {}
            for key in search ['details'] :
                if key in valid_details :
                    result [_count][key] = valid_details [key] (elt)
            _count += 1
            if max_count_present and max_count < _count :
                break
            if max_delay_present and max_delay < (datetime.datetime.now () - _t0).total_seconds() :
                break
        del (elements)

    database.close()

    result ['ok'] = True

    return result
