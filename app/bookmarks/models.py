from datetime import datetime
import collections

from app import db


class Bookmark(db.Model):
    __tablename__ = "bookmarks"

    id = db.Column(db.Integer(), primary_key=True)
    title = db.Column(db.String())
    created = db.Column(db.DateTime, default=datetime.utcnow)
    items = db.relationship("Item", cascade="all,delete,delete-orphan", 
                            backref="bookmark")

    def add_item(self, *args, commit=True, **kwargs):
        '''Adds item to the bookmark.'''
        if len(args) > 0 and isinstance(args[0], Item):
            item = args[0]
        else:
            item = Item(*args, **kwargs)
            db.session.add(item)

        self.items.append(item)
        if commit:
            db.session.commit()
        return item

    def update(self, data=None, commit=True, **kwargs):
        '''Update bookmark on the base of dict or **kwargs.'''
        if not data:
            data = kwargs
        else:
            if not isinstance(data, collections.Mapping):
                raise TypeError("first argument must be dictionary")

        if "title" in data:
            self.title = data["title"]
        if "items" in data:
            self.items.extend(data["items"])

        if commit:
            db.session.commit()

    def remove_item(self, item, commit=True):
        '''Remove item for the bookmark.'''
        if not isinstance(item, Item):
            item = Item.query.get(item)
        if item:
            self.items.remove(item)

    def to_dict(self, timezone=None):
        if timezone:
            created = utc2tz(self.created, timezone)
        else:
            created = self.created

        return {"id": self.id, "title": self.title, "created": created,
                "items": [ item.get_info(timezone) for item in self.items]}

    def get_info(self, timezone=None):
        if timezone:
            created = utc2tz(self.created, timezone)
        else:
            created = self.created

        return {"id": self.id, "title": self.title,
                "created": created}


class Item(db.Model):
    __tablename__ = "items"

    id = db.Column(db.Integer(), primary_key=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    bookmark_id = db.Column(db.Integer(), db.ForeignKey("bookmarks.id"))
    desc = db.Column(db.String())
    value = db.Column(db.String())


    def update(self, data=None, commit=True, **kwargs):
        '''Update item on the base of dict or **kwargs.'''
        if not data:
            data = kwargs
        else:
            if not isinstance(data, collections.Mapping):
                raise TypeError("first argument must be dictionary")

        # Update fields which can be update (not read-only fields)
        update_possible = {"value", "desc", "bookmark_id"}
        fields_to_update = update_possible & set(data.keys())
        for field in fields_to_update:
            setattr(self, field, data[field])

        if commit:
            db.session.commit()

    def to_dict(self, timezone=None):
        if timezone:
            created = utc2tz(self.created, timezone)
        else:
            created = self.created

        return {
            "id": self.id, "created": created,
            "value": self.value, "desc": self.desc,
            "bookmark_id": self.bookmark_id
            }

    def get_info(self, timezone=None):
        return self.to_dict()