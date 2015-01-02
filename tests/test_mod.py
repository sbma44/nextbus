import nextbus

def test_g2():
    nb = nextbus.Nextbus({'G2': 'http://www.nextbus.com/api/pub/v1/agencies/wmata/routes/G2/stops/6596/predictions?coincident=true&direction=G2_G2_0'})
    nb.refresh('G2')
    print nb.predictions