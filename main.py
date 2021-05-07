from flask import Flask, request, jsonify
from flask_restful import Api, Resource, fields, marshal_with, abort
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
api = Api(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --------------------------MODELS-------------------------

class HotelRoomModel(db.Model):
    room_id = db.Column(db.Integer, primary_key=True)
    roomNumber = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(200), nullable=False)
    numberOfSeats = db.Column(db.Integer, nullable=False)


class GuestModel(db.Model):
    guest_id = db.Column(db.Integer, primary_key=True)
    FIO = db.Column(db.String(200), nullable=False)
    birthday = db.Column(db.String(50), nullable=False)
    hotelRoomNumber = db.Column(db.Integer, nullable=False)


db.create_all()
# --------------------------MODELS-------------------------

# ---------------------------JSONSERIALIZE----------------
guest_fields = {
    'guest_id': fields.Integer,
    'FIO': fields.String,
    'birthday': fields.String,
    'hotelRoomNumber': fields.Integer
}

hotelRoom_fields = {
    'room_id': fields.Integer,
    'roomNumber': fields.Integer,
    'description': fields.String,
    'numberOfSeats': fields.Integer
}


# ---------------------------JSONSERIALIZE----------------

# ----------------------HOTELROOM--------------------------

class HotelRoom(Resource):
    @marshal_with(hotelRoom_fields)
    def get(self, room_id):
        room = HotelRoomModel.query.get(room_id)
        if not room:
            abort(404, message="Could not find room with that id")

        guests = GuestModel.query.filter_by(hotelRoomNumber=room.roomNumber).all()
        res = {'room_id': room.room_id,
               'roomNumber': room.roomNumber,
               'description': room.description,
               'numberOfSeats': room.numberOfSeats,
               'Guests': [{'guest_id': g.guest_id,
                           'FIO': g.FIO,
                           'birthday': g.birthday} for g in guests]}

        return jsonify(res)

    @marshal_with(hotelRoom_fields)
    def post(self, room_id):
        room = GuestModel.query.get(room_id)
        if room:
            abort(404, message="HotelRoom with that id already exist")

        newHotelRoom = HotelRoomModel(
            room_id=room_id,
            roomNumber=request.json['roomNumber'],
            description=request.json['description'],
            numberOfSeats=request.json['numberOfSeats'],
        )
        db.session.add(newHotelRoom)
        db.session.commit()

        return newHotelRoom

    def put(self, room_id):
        hotelRoom = HotelRoomModel.query.filter_by(room_id=room_id).first()
        if not hotelRoom:
            abort(404, message="HotelRoom doesn't exist, cannot update")
        data = request.json
        if 'room_id' in data:
            hotelRoom.room_id = data['room_id']
        if 'roomNumber' in data:
            hotelRoom.roomNumber = data['roomNumber']
        if 'description' in data:
            hotelRoom.description = data['description']
        if 'numberOfSeats' in data:
            hotelRoom.numberOfSeats = data['numberOfSeats']
        db.session.commit()
        guests = GuestModel.query.filter_by(hotelRoomNumber=hotelRoom.roomNumber).all()
        res = {'room_id': hotelRoom.room_id,
               'roomNumber': hotelRoom.roomNumber,
               'description': hotelRoom.description,
               'numberOfSeats': hotelRoom.numberOfSeats,
               'Guests': [{'guest_id': g.guest_id,
                           'FIO': g.FIO,
                           'birthday': g.birthday} for g in guests]}

        return jsonify(res)

    def delete(self, room_id):
        hotelRoom = HotelRoomModel.query.get(room_id)
        db.session.delete(hotelRoom)
        db.session.commit()
        return '', 204


class HotelRoomList(Resource):
    def get(self):
        rooms = HotelRoomModel.query.all()
        result = []
        for hotelRoom in rooms:
            guests = GuestModel.query.filter_by(hotelRoomNumber=hotelRoom.roomNumber).all()
            room_info = {'room_id': hotelRoom.room_id,
                         'roomNumber': hotelRoom.roomNumber,
                         'description': hotelRoom.description,
                         'numberOfSeats': hotelRoom.numberOfSeats,
                         'Guests': [{'guest_id': g.guest_id,
                                     'FIO': g.FIO,
                                     'birthday': g.birthday} for g in guests]}
            result.append(room_info)
        return jsonify(result)


# ----------------------HOTELROOM--------------------------

# ----------------------GUEST--------------------------
class Guest(Resource):
    def get(self, guest_id):
        result = GuestModel.query.get(guest_id)
        if not result:
            abort(404, message="Could not find guest with that id")

        room = HotelRoomModel.query.filter_by(roomNumber=result.hotelRoomNumber).first()
        res = {'guest_id': result.guest_id, 'FIO': result.FIO, 'birthday': result.birthday,
               'Room': {'room_id': room.room_id,
                        'roomNumber': room.roomNumber,
                        'description': room.description,
                        'numberOfSeats': room.numberOfSeats}}
        return jsonify(res)

    def post(self, guest_id):
        guest = GuestModel.query.get(guest_id)
        if guest:
            abort(404, message="Guest with that id already exist")
        guests = GuestModel.query.filter_by(hotelRoomNumber=request.json['hotelRoomNumber']).all()
        room = HotelRoomModel.query.filter_by(roomNumber=request.json['hotelRoomNumber']).first()
        if len(guests) >= room.numberOfSeats:
            abort(404, message="All seats are taken")
        if guest:
            abort(404, message="Guest with that id already exist")
        newGuest = GuestModel(
            guest_id=guest_id,
            FIO=request.json['FIO'],
            birthday=request.json['birthday'],
            hotelRoomNumber=request.json['hotelRoomNumber'],
        )
        room = HotelRoomModel.query.filter_by(roomNumber=newGuest.hotelRoomNumber).first()
        if not room:
            abort(404, message="Could not find hotelRoom with that roomNumber")
        db.session.add(newGuest)
        db.session.commit()
        result = {'guest_id': newGuest.guest_id, 'FIO': newGuest.FIO, 'birthday': newGuest.birthday,
                  'Room': {'room_id': room.room_id,
                           'roomNumber': room.roomNumber,
                           'description': room.description,
                           'numberOfSeats': room.numberOfSeats}}
        return jsonify(result)

    def put(self, guest_id):
        guest = GuestModel.query.filter_by(guest_id=guest_id).first()
        if not guest:
            abort(404, message="Guest doesn't exist, cannot update")
        data = request.json
        if 'guest_id' in data:
            guest.guest_id = data['guest_id']
        if 'FIO' in data:
            guest.FIO = data['FIO']
        if 'birthday' in data:
            guest.birthday = data['birthday']
        if 'hotelRoomNumber' in data:
            guest.hotelRoomNumber = data['hotelRoomNumber']
        db.session.commit()
        room = HotelRoomModel.query.filter_by(roomNumber=guest.hotelRoomNumber).first()
        result = {'guest_id': guest.guest_id, 'FIO': guest.FIO, 'birthday': guest.birthday,
                  'Room': {'room_id': room.room_id,
                           'roomNumber': room.roomNumber,
                           'description': room.description,
                           'numberOfSeats': room.numberOfSeats}}
        return jsonify(result)

    def delete(self, guest_id):
        guest = GuestModel.query.get(guest_id)
        db.session.delete(guest)
        db.session.commit()
        return '', 204


class GuestList(Resource):
    def get(self):
        guests = GuestModel.query.all()
        result = []
        for guest in guests:
            room = HotelRoomModel.query.filter_by(roomNumber=guest.hotelRoomNumber).first()
            guest_info = {'guest_id': guest.guest_id, 'FIO': guest.FIO, 'birthday': guest.birthday,
                          'Room': {'room_id': room.room_id,
                                   'roomNumber': room.roomNumber,
                                   'description': room.description,
                                   'numberOfSeats': room.numberOfSeats}}
            result.append(guest_info)
        return jsonify(result)


# ----------------------GUEST--------------------------


api.add_resource(HotelRoom, "/hotelroom/<int:room_id>")
api.add_resource(HotelRoomList, "/hotelroomlist")
api.add_resource(Guest, "/guest/<int:guest_id>")
api.add_resource(GuestList, "/guestlist")

if __name__ == "__main__":
    app.run(debug=True)
