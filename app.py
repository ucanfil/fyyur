#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
import sys
from flask import Flask, render_template, request, Response, abort, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import FlaskForm
from forms import *
from pprint import pprint

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db = SQLAlchemy(app, session_options={"expire_on_commit": False})
migrate = Migrate(app, db)


#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#
class Show(db.Model):
    __tablename__ = 'Show'

    venue_id = db.Column(db.Integer, db.ForeignKey(
        'Venue.id'), primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'Artist.id'), primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)

    venue = db.relationship('Venue', back_populates='artists')
    artist = db.relationship('Artist', back_populates='venues')


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), server_default="{}")
    website = db.Column(db.String(120))
    seeking_talent = db.Column(db.Boolean, nullable=True, server_default='f')
    seeking_description = db.Column(db.String(500), nullable=True)
    artists = db.relationship('Show', back_populates='venue')


class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String), server_default="{'other'}")
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=True, server_default='f')
    seeking_description = db.Column(db.String(500), nullable=True)
    website = db.Column(db.String(120))
    venues = db.relationship('Show', back_populates='artist')


db.create_all()

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

# def format_datetime(value, format='medium'):
#   date = dateutil.parser.parse(value)
#   if format == 'full':
#       format="EEEE MMMM, d, y 'at' h:mma"
#   elif format == 'medium':
#       format="EE MM, dd, y h:mma"
#   return babel.dates.format_datetime(date, format)

# app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    data = []

    venues = Venue.query.with_entities(func.count().label('num_upcoming_shows'), Venue.id.label(
        'id'), Venue.city.label('city'), Venue.state.label('state'), Venue.name.label('name')).join(Show, (Show.venue_id == Venue.id) & (Show.start_time > datetime.now())).group_by(Venue.id).all()

    for venue in venues:
        found = False

        for d in data:
            if d['state'] == venue.state and d['city'] == venue.city:
                found = True
                d['venues'].append({
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows': venue.num_upcoming_shows
                })
                break

        if not found:
            data.append({
                'state': venue.state,
                'city': venue.city,
                'venues': [{
                    'id': venue.id,
                    'name': venue.name,
                    'num_upcoming_shows': venue.num_upcoming_shows,
                }]
            })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():

    search_term = request.form.get('search_term', '')

    result = Venue.query.with_entities(Venue.id.label(
        'id'), Venue.name.label('name'), func.count().label('num_upcoming_shows')).join(Show, (Show.venue_id == Venue.id) & (Show.start_time > datetime.now())).filter(Venue.name.ilike('%'+search_term+'%')).group_by(Venue.id).all()

    response = {
        "count": len(result),
        "data": result
    }

    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):

    venue = Venue.query.get(venue_id)
    venue.past_shows = []
    venue.upcoming_shows = []
    venue.past_shows_count = 0
    venue.upcoming_shows_count = 0

    shows = Venue.query.join(Show, Show.venue_id == Venue.id).join(Artist, Artist.id == Show.artist_id).add_columns(Show.start_time.label('start_time'), Artist.id.label(
        'artist_id'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link')).filter(Venue.id == venue_id).order_by(Show.start_time.desc()).all()

    for show in shows:
        if show.start_time < datetime.now():
            venue.past_shows.append(show)
            venue.past_shows_count = venue.past_shows_count + 1
        else:
            venue.upcoming_shows.append(show)
            venue.upcoming_shows_count = venue.upcoming_shows_count + 1

    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    form = VenueForm()
    error = False

    if form.validate_on_submit():
        try:
            venue = Venue(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                address=form.address.data,
                phone=form.phone.data,
                website=form.website.data,
                image_link=form.image_link.data,
                genres=form.genres.data,
                facebook_link=form.facebook_link.data,
            )
            db.session.add(venue)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()

        if error:
            abort(400)
        else:
            flash('Venue ' + venue.name + ' was successfully listed!')

            return render_template('pages/home.html')

    flash('An error occurred. Venue ' +
          form.name.data + ' could not be listed.')

    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/<venue_id>', methods=['POST'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    error = False

    try:
      Venue.query.filter_by(id = venue_id).delete()
      db.session.commit()
    except:
      error = True
      db.session.rollback()
      print(sys.exc_info())
    finally:
      db.session.close()

    if error:
      abort(400)
    else:
      return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():

    return render_template('pages/artists.html', artists=Artist.query.all())


@app.route('/artists/search', methods=['POST'])
def search_artists():

    search_term = request.form.get('search_term', '')

    result = Artist.query.with_entities(Artist.id.label(
        'id'), Artist.name.label('name'), func.count().label('num_upcoming_shows')).join(Show, (Show.artist_id == Artist.id) & (Show.start_time > datetime.now())).filter(Artist.name.ilike('%'+search_term+'%')).group_by(Artist.id).all()

    response = {
        "count": len(result),
        "data": result,
    }

    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):

    artist = Artist.query.get(artist_id)
    artist.past_shows = []
    artist.upcoming_shows = []
    artist.past_shows_count = 0
    artist.upcoming_shows_count = 0

    shows = Artist.query.join(Show, Show.artist_id == Artist.id).join(Venue, Venue.id == Show.venue_id).add_columns(Show.start_time.label('start_time'), Artist.id.label(
        'artist_id'), Artist.name.label('artist_name'), Venue.image_link.label('venue_image_link')).filter(Artist.id == artist_id).order_by(Show.start_time.desc()).all()

    for show in shows:
        if show.start_time < datetime.now():
            artist.past_shows.append(show)
            artist.past_shows_count = artist.past_shows_count + 1
        else:
            artist.upcoming_shows.append(show)
            artist.upcoming_shows_count = artist.upcoming_shows_count + 1

    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    artist = Artist.query.get(artist_id)
    form = ArtistForm()

    form.name.data = artist.name
    form.city.data = artist.city
    form.state.data = artist.state
    form.phone.data = artist.phone
    form.genres.data = artist.genres
    form.image_link.data = artist.image_link
    form.facebook_link.data = artist.facebook_link
    form.website.data = artist.website

    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):

    form = ArtistForm()
    error = False

    artist = Artist.query.get(artist_id)

    if form.validate_on_submit():
        try:
            artist.name = form.name.data
            artist.city = form.city.data
            artist.state = form.state.data
            artist.phone = form.phone.data
            artist.website = form.website.data
            artist.image_link = form.image_link.data
            artist.genres = form.genres.data
            artist.facebook_link = form.facebook_link.data
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()

        if error:
            abort(400)
        else:
            flash('Artist ' + artist.name + ' was successfully edited!')

            return redirect(url_for('show_artist', artist_id=artist_id))

    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):

    venue = Venue.query.get(venue_id)
    form = VenueForm()

    form.name.data = venue.name
    form.city.data = venue.city
    form.state.data = venue.state
    form.address.data = venue.address
    form.phone.data = venue.phone
    form.genres.data = venue.genres
    form.image_link.data = venue.image_link
    form.facebook_link.data = venue.facebook_link
    form.website.data = venue.website

    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):

    form = VenueForm()
    error = False

    venue = Venue.query.get(venue_id)

    if form.validate_on_submit():
        try:
            venue.name = form.name.data
            venue.city = form.city.data
            venue.state = form.state.data
            venue.address = form.address.data
            venue.phone = form.phone.data
            venue.website = form.website.data
            venue.image_link = form.image_link.data
            venue.genres = form.genres.data
            venue.facebook_link = form.facebook_link.data
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()

        if error:
            abort(400)
        else:
            flash('Venue ' + venue.name + ' was successfully edited!')

            return redirect(url_for('show_venue', venue_id=venue_id))

    return redirect(url_for('edit_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():

    error = False
    form = ArtistForm()

    if form.validate_on_submit():
        try:
            artist = Artist(
                name=form.name.data,
                city=form.city.data,
                state=form.state.data,
                phone=form.phone.data,
                genres=form.genres.data,
                image_link=form.image_link.data,
                facebook_link=form.facebook_link.data,
                website=form.website.data,
            )
            db.session.add(artist)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()

        if error:
            abort(400)
        else:
            flash('Artist ' + request.form['name'] +
                  ' was successfully listed!')

            return render_template('pages/home.html')

    flash('An error occurred. Artist ' +
          form.name.data + ' could not be listed.')

    return render_template('forms/new_artist.html', form=form)


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():

    shows = Show.query.join(Artist, Artist.id == Show.artist_id).join(Venue, Venue.id == Show.venue_id).add_columns(Show.venue_id, Show.artist_id, Venue.name.label(
        'venue_name'), Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Show.start_time).order_by(Show.start_time.desc()).all()

    return render_template('pages/shows.html', shows=shows)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():

    form = ShowForm()
    error = False

    print(form.start_time.data)

    if form.validate_on_submit():
        try:
            show = Show(
                venue_id=form.venue_id.data,
                artist_id=form.artist_id.data,
                start_time=form.start_time.data,
            )
            db.session.add(show)
            db.session.commit()
        except:
            error = True
            db.session.rollback()
            print(sys.exc_info())
        finally:
            db.session.close()

        if error:
            flash('An error occurred. Show could not be listed.')
            abort(400)
        else:
            flash('Show was successfully listed!')

            return render_template('pages/home.html')

    else:
        return render_template('forms/new_show.html', form=form)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
