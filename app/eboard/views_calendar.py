from flask import render_template, flash, current_app, \
                    redirect, url_for, send_from_directory, send_file, \
                    request
from flask_login import login_required
from app.eboard import eboard 
from sqlalchemy.orm import subqueryload, joinedload

from app import db
from app.models import Event

import datetime
import json

@eboard.route("/calendar")
@login_required
def calendar():
    return render_template("eboard/calendar.html")

@eboard.route("/calendar/events/source", methods=["GET", "POST"])
@login_required
def events_source():
    start_date = datetime.datetime.strptime(request.values.get("start"), "%Y-%m-%d")
    end_date = datetime.datetime.strptime(request.values.get("end"), "%Y-%m-%d")

    events = db.session.query(Event).options(subqueryload(Event.task).\
        joinedload("status")).filter(~((Event.end < start_date) | 
        (Event.start > end_date))).all()

    return json.dumps([ event.move2dict() for event in events if \
        event.task is None or event.task.status.name == "active"]), 200

@eboard.route("/calendar/events/get", methods=["GET", "POST"])
@login_required
def events_get():
    event_id = request.json.get("id")
    event = Event.query.filter(Event.id == int(event_id)).one_or_none()
    if event:
        return json.dumps({"status": "success", "data": event.move2dict()}), 200
    return json.dumps({"status": "failure", "data": {"info": "Lack of event record."}}), 200

@eboard.route("/calendar/events/put", methods=["GET", "POST"])
@login_required
def events_put():
    title = request.json.get("title")
    description = request.json.get("description")
    start = datetime.datetime.strptime(request.json.get("start"), "%Y-%m-%d %H:%M")
    end = datetime.datetime.strptime(request.json.get("end"), "%Y-%m-%d %H:%M")
    all_day = request.json.get("allday") == "yes"

    if all_day: # update start and end data for all day events
        start = datetime.datetime(start.year, start.month, start.day, 0, 0, 0)
        end = datetime.datetime(end.year, end.month, end.day, 0, 0, 0)

    event = Event(title = title, description = description,\
            start = start, end = end, allDay = all_day)
    db.session.add(event)
    db.session.commit()

    return json.dumps({"status": "success", "data": event.move2dict()})

@eboard.route("/calendar/events/update", methods=["GET", "POST"])
@login_required
def events_update():
    event_id = request.json.get("id")
    event = Event.query.filter(Event.id == int(event_id)).one_or_none()
    if event:
        if request.json.get("title"):
            event.title = request.json.get("title")
        if request.json.get("description"):
            event.description = request.json.get("description")

        if request.json.get("allday"): # update start and end data for all day events
            start = datetime.datetime.strptime(request.json.get("start"), "%Y-%m-%d %H:%M")
            start = datetime.datetime(start.year, start.month, start.day, 0, 0, 0)
            end = datetime.datetime(start.year, start.month, start.day, 23, 59, 59)

            event.start = start
            event.end = end
            event.allDay = True
        else:
            if request.json.get("start"):
                event.start = datetime.datetime.strptime(request.json.get("start"), "%Y-%m-%d %H:%M")
            if request.json.get("end"):
                event.end = datetime.datetime.strptime(request.json.get("end"), "%Y-%m-%d %H:%M")
            else:
                if event.allDay: # drag from allDay to ordinal 
                    event.end = event.start + datetime.timedelta(hours = 2)
                    event.allDay = False

        db.session.commit()
        return json.dumps({"status": "success", "data": event.move2dict()})
    else:
        return json.dumps({"status": "failure", "data": {"info": "Lack of event record."}}), 200    

@eboard.route("/calendar/events/remove", methods=["GET", "POST"])
@login_required
def events_remove():
    event_id = request.json.get("id")
    event = Event.query.filter(Event.id == int(event_id)).one_or_none()
    if event:
        db.session.delete(event)
        db.session.commit()
        return json.dumps({"status": "success", "data": {"id": event_id}}), 200
    return json.dumps({"status": "failure", "data":{"inof": "Lack of event record"}}), 200