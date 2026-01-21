from airflow.models import BaseOperator
from airflow.exceptions import AirflowException
from typing import Dict, Any, Optional, Sequence
import random
from datetime import datetime

class WeatherFetchOperator(BaseOperator):
    """
    Fetches weather data for a specified city using mock data for testing.
    
    This operator generates realistic mock weather data including temperature,
    description, humidity, wind speed, and other weather metrics. The data
    is city-specific with appropriate temperature ranges for realism.
    
    Args:
        city (str): Name of the city to fetch weather for
        country_code (str, optional): ISO country code (e.g., JP, US, GB)
        units (str, optional): Temperature units - 'metric' or 'imperial'. Defaults to 'metric'
    
    Returns:
        dict: Weather data dictionary containing temperature, description, humidity, etc.
    """
    
    template_fields: Sequence[str] = ['city', 'country_code', 'units']
    ui_color: str = "#87CEEB"
    
    def __init__(
        self,
        city: str,
        country_code: Optional[str] = None,
        units: str = 'metric',
        **kwargs
    ):
        super().__init__(**kwargs)
        
        # Validate units if not a template
        if '{{' not in str(units) and units not in ['metric', 'imperial']:
            raise AirflowException(f"Invalid units '{units}'. Must be 'metric' or 'imperial'")
        
        self.city = city
        self.country_code = country_code
        self.units = units
        
        # City-specific temperature ranges (Celsius)
        self._city_temp_ranges = {
            'london': (-2, 25),
            'new york': (-10, 30),
            'tokyo': (-5, 35),
            'sydney': (5, 40),
            'moscow': (-25, 25),
            'mumbai': (15, 45),
            'cairo': (5, 45),
            'reykjavik': (-15, 15),
            'singapore': (22, 35),
            'anchorage': (-25, 20),
            'miami': (10, 35),
            'dubai': (10, 50),
            'stockholm': (-15, 25),
            'bangkok': (20, 40),
            'cape town': (5, 30)
        }
        
        self._weather_descriptions = [
            'Clear sky',
            'Few clouds',
            'Scattered clouds',
            'Broken clouds',
            'Overcast clouds',
            'Light rain',
            'Moderate rain',
            'Heavy rain',
            'Light snow',
            'Moderate snow',
            'Mist',
            'Fog',
            'Thunderstorm',
            'Drizzle',
            'Partly cloudy'
        ]
        
        self.log.info(f"Initialized WeatherFetchOperator for city: {city}, units: {units}")
    
    def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the weather fetch operation and return mock weather data.
        
        Args:
            context: Airflow context dictionary
            
        Returns:
            dict: Weather data dictionary
            
        Raises:
            AirflowException: If validation fails or execution encounters an error
        """
        self.log.info(f"Executing WeatherFetchOperator for task: {self.task_id}")
        
        # Validate template fields after Jinja rendering
        if self.units not in ['metric', 'imperial']:
            raise AirflowException(f"Invalid units '{self.units}'. Must be 'metric' or 'imperial'")
        
        if not self.city or not isinstance(self.city, str):
            raise AirflowException("City must be a non-empty string")
        
        try:
            # Generate mock weather data
            weather_data = self._generate_mock_weather_data()
            
            self.log.info(f"Successfully fetched weather data for {self.city}: "
                         f"{weather_data['temperature']}°{'C' if self.units == 'metric' else 'F'}, "
                         f"{weather_data['description']}")
            
            return weather_data
            
        except Exception as e:
            self.log.error(f"Failed to fetch weather data for {self.city}: {str(e)}")
            raise AirflowException(f"Weather fetch failed: {str(e)}")
    
    def _generate_mock_weather_data(self) -> Dict[str, Any]:
        """
        Generate realistic mock weather data for the specified city.
        
        Returns:
            dict: Mock weather data
        """
        city_lower = self.city.lower()
        
        # Get city-specific temperature range or use default
        temp_range = self._city_temp_ranges.get(city_lower, (-10, 35))
        
        # Generate base temperature in Celsius
        temp_celsius = random.uniform(temp_range[0], temp_range[1])
        
        # Convert to requested units
        if self.units == 'imperial':
            temperature = round((temp_celsius * 9/5) + 32, 1)
            temp_unit = 'F'
            wind_speed_unit = 'mph'
            wind_speed = round(random.uniform(0, 25), 1)
        else:
            temperature = round(temp_celsius, 1)
            temp_unit = 'C'
            wind_speed_unit = 'm/s'
            wind_speed = round(random.uniform(0, 15), 1)
        
        # Generate other weather parameters
        humidity = random.randint(20, 95)
        pressure = random.randint(980, 1030)
        visibility = round(random.uniform(1, 20), 1)
        cloud_cover = random.randint(0, 100)
        
        # Select weather description based on cloud cover and other factors
        if cloud_cover < 10:
            description = 'Clear sky'
        elif cloud_cover < 25:
            description = 'Few clouds'
        elif cloud_cover < 50:
            description = 'Scattered clouds'
        elif cloud_cover < 85:
            description = 'Broken clouds'
        else:
            description = random.choice(self._weather_descriptions)
        
        # Generate wind direction
        wind_directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        wind_direction = random.choice(wind_directions)
        
        weather_data = {
            'city': self.city,
            'country_code': self.country_code,
            'temperature': temperature,
            'temperature_unit': temp_unit,
            'feels_like': round(temperature + random.uniform(-3, 3), 1),
            'description': description,
            'humidity': humidity,
            'pressure': pressure,
            'pressure_unit': 'hPa',
            'wind_speed': wind_speed,
            'wind_speed_unit': wind_speed_unit,
            'wind_direction': wind_direction,
            'visibility': visibility,
            'visibility_unit': 'km',
            'cloud_cover': cloud_cover,
            'uv_index': random.randint(1, 11),
            'timestamp': datetime.now().isoformat(),
            'units': self.units
        }
        
        return weather_data