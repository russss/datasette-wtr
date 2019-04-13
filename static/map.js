var marker_icon_tx = L.icon({
    iconUrl: '/static/marker-tx.svg',
    iconSize: [30, 40],
    iconAnchor: [15, 30]
});

var marker_icon_rx = L.icon({
    iconUrl: '/static/marker-rx.svg',
    iconSize: [30, 40],
    iconAnchor: [15, 30]
});

var marker_icon_tx_omni = L.icon({
    iconUrl: '/static/marker-tx-omni.svg',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
});

var marker_icon_rx_omni = L.icon({
    iconUrl: '/static/marker-rx-omni.svg',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
});

function fetchRows(sql, pk, from_id) {
    return fetch('/wtr-' + database_hash +'.json?sql=' + encodeURIComponent(sql) + '&pk=' + pk + '&from_id=' + from_id + '&_shape=objects').then(r => r.json());
}

function insertMap(sql) {
    var pk = decodeURIComponent(location.pathname.split('/').slice(-1)[0]);
    fetchRows(sql, pk, 0).then(createMap.bind(this, sql, pk))
}

function createMarker(row) {
    var gj = JSON.parse(row['geometry']);
    var title = `License: <a href="/wtr/license/${encodeURIComponent(row['license'])}">${row['license']}</a>` +
        "<br>Frequency: " + row['frequency'] / 1000000 + " MHz";

    if (row['tx_rx'] == 'T') {
        if (row['azimuth']) {
            var icon = marker_icon_tx;
        } else {
            var icon = marker_icon_tx_omni;
        }
        title += " (Tx)";
    } else if (row['tx_rx'] == 'R') {
        if (row['azimuth']) {
            var icon = marker_icon_rx;
        } else {
            var icon = marker_icon_rx_omni;
        }
        title += " (Rx)";
    } else {
        var icon = new L.Icon.Default;
    }

    if (row['azimuth']) {
        title += `<br>Azimuth: ${row['azimuth']}°`;
    }

    var marker = L.marker(new L.LatLng(gj.coordinates[1], gj.coordinates[0]), {icon: icon, rotationAngle: row['azimuth']})
    marker.bindPopup(title);
    return marker;
}

function loadMore(sql, pk, from_id, layer) {
    console.log(`Loading more from ${from_id}`);
    fetchRows(sql, pk, from_id, layer).then(function(d) {
        var markers = [];
        for (var row of d.rows) {
            markers.push(createMarker(row));
        }
        layer.addLayers(markers, {'chunkedLoading': true})
        if (d.truncated) {
            loadMore(sql, pk, d.rows[d.rows.length - 1]['pk'], layer);
        }
    })
}

function createMap(sql, pk, d) {
    if (d.rows.length == 0) {
        return;
    }

    var tiles = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        maxZoom: 19,
        detectRetina: true,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    });

    var map = L.map('map', {layers: [tiles]});
    var markers = [];

    for (var row of d.rows) {
        markers.push(createMarker(row));
    }

    var layer;
    if (d.rows.length > 2) {
        layer = L.markerClusterGroup({chunkedLoading: true});
        layer.addTo(map);       
        layer.addLayers(markers, {
            'chunkedLoading': true   
        });
        if (d.truncated) {
            loadMore(sql, pk, d.rows[d.rows.length - 1]['pk'], layer);
        }
    } else {
        layer = L.featureGroup(markers);
        layer.addTo(map);
    }

    map.fitBounds(layer.getBounds());
    if (map.getZoom() > 9) {
        map.setZoom(9);
    }
}
