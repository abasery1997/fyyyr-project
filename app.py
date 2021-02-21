#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from typing import final
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
import config
from models import Venue,Artist,Show,db,app
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

moment = Moment(app)
app.config.from_object('config')
migrate = Migrate(app, db)


app.config['SQLALCHEMY_DATABASE_URI'] = config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = config.SQLALCHEMY_TRACK_MODIFICATIONS

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime

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
    venues = Venue.query.all()

    # prevent any dublicated venues
    cities = set()
    for venue in venues:
        # adding city and  state
        cities.add((venue.city, venue.state))

    data = []
    for city in cities:
        data.append({
            "city": city[0],
            "state": city[1],
            "venues": []
        })
        
    for venue in venues:
        Upshows = 0

        shows = Show.query.filter_by(venue_id=venue.id).all()
        date = datetime.now()

        for show in shows:
            if show.start_time > date:
                Upshows += 1

        for venue_position in data:
            if venue.state == venue_position['state'] and venue.city == venue_position['city']:
                venue_position['venues'].append({
                    "id": venue.id,
                    "name": venue.name,
                    "num_upcoming_shows": Upshows
                })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():

    search_term = request.form.get('search_term', '')
    venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))
    data = []
    for venue in venues:
        data.append({
            "id": venue.id,
            "name": venue.name
        })
    response = {
        "count": venues.count(),
        "data": data
    }

    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    current_time = datetime.now()
    past_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time<current_time).all()
    past_shows = []
    upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.venue_id==venue_id).filter(Show.start_time>current_time).all()
    up_shows = []

    
    for show in past_shows_query:
        data = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        }
        past_shows.append(data)

    for show in upcoming_shows_query:
        data = {
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        }
        up_shows.append(data)
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": up_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(up_shows)
    }
    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

    try:
        # get form data and create
        form = VenueForm()
        venue = Venue(name=form.name.data, city=form.city.data, state=form.state.data, address=form.address.data,
                      phone=form.phone.data, image_link=form.image_link.data, genres=form.genres.data,
                      facebook_link=form.facebook_link.data, seeking_description=form.seeking_description.data,
                      website=form.website.data, seeking_talent=form.seeking_talent.data)
        # coomit session to database
        db.session.add(venue)
        db.session.commit()
        # creation success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        # creation failure
        db.session.rollback()
        flash('some thing went wrong. Venue' +
              request.form['name'] + ' could not be added')
    finally:
        # closes session
        db.session.close()

    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    artists = Artist.query.all()
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():

    search_term = request.form.get('search_term', '')

    artists = Artist.query.filter_by(Artist.name.ilike(f'%{ search_term }%'))
    data = []
    for artist in artists:
        data.append({
            "id": artist.id,
            "name": artist.name
        })
    response = {
        "count": artists.count(),
        "data": data
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the venue page with the given venue_id
    artist = Artist.query.get(artist_id)
   # shows = Show.query.filter_by(artist_id=artist_id).all()
    time_now = datetime.now()
    past_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time<time_now).all()
    past_shows = []
    up_shows_query = db.session.query(Show).join(Venue).filter(Show.artist_id==artist_id).filter(Show.start_time>time_now).all()
    up_shows = []
  
    for show in past_shows_query:
        data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue+image_link": show.venue.image_link,
            "start_time": format_datetime(str(show.start_time))
        }
        past_shows.append(data)
    
    for show in up_shows_query:
        data = {
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "venue+image_link": show.venue.image_link,
            "start_time": format_datetime(str(show.start_time))
        }
        up_shows.append(data)
        

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": up_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(up_shows)
    }

    return render_template('pages/show_artist.html', artist=data)

#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    form = ArtistForm()
    try:
        artist = Artist(name=form.name.data, city=form.city.data, state=form.state.data,
                        phone=form.phone.data, image_link=form.image_link.data, genres=form.genres.data,
                        facebook_link=form.facebook_link.data, seeking_description=form.seeking_description.data,
                        website=form.website.data, seeking_venue=form.seeking_venue.data)

      # coomit session to database
        db.session.add(artist)
        db.session.commit()
        # creation sucess
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except:
      # creation failure
        db.session.rollback()
        flash('some thing went wrong. Artists' +
              request.form['name'] + ' could not be added')
    finally:
      # closes session
        db.session.close()
    return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    shows =Show.query.all()
    data = []
    for show in shows:
        data.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": format_datetime(str(show.start_time))
        })
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    form = ShowForm()

    artist = Artist.query.get(form.artist_id.data)
    try:
        show = Show(artist_id=form.artist_id.data,
                    venue_id=form.venue_id.data, start_time=form.start_time.data)

        db.session.add(show)
        db.session.commit()
        # creation sucess
        flash('Show  of Artist' + artist.name + 'was successfully listed!')
        
    except:
      # creation failure
        db.session.rollback()
        flash('some thing went wrong. Show  of Artist' +
              artist.name + 'was not listed!')
    finally:
      # closes session
        db.session.close()

    return render_template('pages/home.html')


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
