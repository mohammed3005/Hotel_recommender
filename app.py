from ctypes import alignment
from turtle import width, window_width
from flask import Flask, flash, redirect, render_template, request, url_for
from folium import plugins
import ipywidgets
from matplotlib.pyplot import margins
import pandas as pd
import numpy as np
import geocoder
import folium

app = Flask(__name__,static_url_path='/static')
app.config['TEMPLATES_AUTO_RELOAD'] = True


#pickle model for hotel review
hotel_review= pd.read_pickle('./data/review.pkl')
cosine=np.load('./data/tagcosine.npy')
#pickle model for hotel attributes or tags
similarity=np.load('./data/tagcosine.npy')
hoteltags_geo=pd.read_pickle('./data/clean_hoteltag.pkl')
feature = list()
hotel_name = ['The Belgrave Hotel', 'Park Plaza Victoria London', 'Vienna Marriott Hotel', 'AZIMUT Hotel Vienna','Villa Opera Drouot', 'A La Villa Madame', 'Amadi Park Hotel', 'Waldorf Astoria Amsterdam', 'Gallery Hotel', 'Hotel Balmes']

for i in hotel_name:
    ch = 1
    v  = list()
    main = list()
    for j in list((hoteltags_geo[hoteltags_geo['hotel_name'].str.contains(i)]['new_tags']))[0]:
        if ch%5 == 0:
            j = str(ch)+ ") " + j.capitalize()
            v.append(j)
            main.append(v)
            v = []
        else:
            j = str(ch)+ ") " + j.capitalize()
            v.append(j)
        ch +=1
    main.append(v)
    feature.append(main)

#function for getting list of hotels based on hotel reviews
def new_recommendations(name,city, cosine_similarities = cosine):
    
    recommended_hotels = []
    
    #get input city index
    city_index= list(hotel_review[hotel_review.city==city].index)
    
    # gettin the index of the hotel that matches the name
    idx = hotel_review[(hotel_review.hotel_name == name)].index[0]
    
    # creating a Series with the similarity scores in descending order
    score_series = pd.Series(cosine_similarities[idx]).sort_values(ascending = False)

    # getting the indexes of the 10 most similar hotels except itself
    top_10_indexes = list(score_series.index)
    
    # populating the list with the names of the top 10 matching hotels
    for i in range(len(top_10_indexes)):
        if top_10_indexes[i] not in city_index:
            pass
        else:
            recommended_hotels.append(hotel_review[hotel_review.index==top_10_indexes[i]]['hotel_name'].values[0])

    
    h = hotel_review[['hotel_name','lat_x','lng_x']].to_dict(orient='records')
    l = {k['hotel_name']: [k['lat_x'], k['lng_x']] for k in h}
    if {hotel: l[hotel] for hotel in recommended_hotels }=={}:
        print("There are no hotels of similar hotel")
    else:
        output= {hotel: l[hotel] for hotel in recommended_hotels[:10]}
        newoutput={i:output for i in range(1,len(output)+1)}
        return newoutput

#function to pin the hotels on folium
def get_hotel(hotel,choise,mydict,city):
    loc2 = geocoder.osm(city)

    # map
    main_map = folium.Map(location=[loc2.lat, loc2.lng], zoom_start=13)
    folium.raster_layers.TileLayer('Open Street Map').add_to(main_map)
    # loop through dict
    for i in range (1,6):
        folium.Marker(location=list(mydict[i].values())[i-1]
                      ,popup=list(mydict[i].keys())[i-1],tooltip=str(list(mydict[i].keys())[i-1]),
                     icon=plugins.BeautifyIcon(number=i,
                                               icon='bus',
                                            border_color='blue',
                                            border_width=0.5,
                                            text_color='red',
                                            inner_icon_style='margin-top:0px;')).add_to(main_map)
    l = list(mydict[1].keys())
    
    feature = list()
    for i in hotel_name:
        ch = 1
        v  = list()
        main = list()
        for j in list((hoteltags_geo[hoteltags_geo['hotel_name'].str.contains(i)]['new_tags']))[0]:
            if ch <= 5:
                v.append(str(str(ch)+")"+j.capitalize()))
            ch += 1
        main.append(v)
        feature.append(main)
    
    main_map.save('templates/map.html')
    return render_template('index.html', feature = feature,name = l[:5], city = city, hotel = hotel)

@app.route('/map')
def map():
    return render_template('map.html')


# function to get recommendation for tags,output as dictionary
def new_recommendations_tags(name,city, cosine_similarities):
    
    recommended_hotels = []
    
    #get input city index
    city_index= list(hoteltags_geo[hoteltags_geo.city==city].index)
    
    # gettin the index of the hotel that matches the name
    idx = hoteltags_geo[(hoteltags_geo.hotel_name == name)].index[0]
    
    # creating a Series with the similarity scores in descending order
    score_series = pd.Series(cosine_similarities[idx]).sort_values(ascending = False)
    # getting the indexes of the 10 most similar hotels except itself
    top_10_indexes = list(score_series.index)

    # populating the list with the names of the top 10 matching hotels
    for i in range(len(top_10_indexes)):
        if top_10_indexes[i] not in city_index:
            pass
        else:
            recommended_hotels.append(hoteltags_geo[hoteltags_geo.index==top_10_indexes[i]]['hotel_name'].values[0])

    h = hoteltags_geo[['hotel_name','lat_x','lng_x']].to_dict(orient='records')
    l = {k['hotel_name']: [k['lat_x'], k['lng_x']] for k in h}
    if {hotel: l[hotel] for hotel in recommended_hotels }=={}:
        print("There are no hotels of similar hotel")
    else:
        output= {hotel: l[hotel] for hotel in recommended_hotels[:10]}
        newoutput={i:output for i in range(1,len(output)+1)}
        return newoutput



@app.route('/')
def new():
    return render_template('new.html', hotel_n = hotel_name, feature = feature,len = len(hotel_name))

@app.route('/result',methods = ['GET','POST'])
def result():
    if request.method == 'POST':
        if request.form['options']=='reviews':
            var_city=request.form['city']
            var_hotel=request.form['hotel']
            return get_hotel(var_hotel,'reviews',mydict=new_recommendations(var_hotel,var_city,cosine_similarities=cosine),city=var_city)
        elif request.form['options']=='tags':
            var_city=request.form['city']
            var_hotel=request.form['hotel']
            return get_hotel(var_hotel,'tags',mydict=new_recommendations_tags(var_hotel,var_city,cosine_similarities=similarity),city=var_city)
    else:
        return render_template('new.html',hotel_n = hotel_name, feature = feature,len = len(hotel_name) )


@app.route('/about')
def about():
    return render_template('about.html')

if __name__ == '__main__':
   app.run(debug = True)