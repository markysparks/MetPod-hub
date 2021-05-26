

def pressure_check(value):
    """Check the pressure value falls within reasonable limits.
    :param value: The pressure value in hectopascals (hPa).
    :return: True if the value falls with limits.
    :raise: ValueError if the value falls outside limits."""
    if 800 < value < 1200:
        return True
    else:
        raise ValueError(str(value) + ' pressure value fails check')


def temperature_check(value):
    """Check the temperature value falls within reasonable limits.
    :param value: The temperature value in degrees C.
    :return: True if the value falls with limits.
    :raise: ValueError if the value falls outside limits."""
    if -100 < value < 100 or value is None:
        return True
    else:
        raise ValueError(str(value) + ' temperature value fails check')


def humidity_check(value):
    """Check the humidity value falls within reasonable limits.
    :param value: The humidity value in per-cent (%).
    :return: True if the value falls with limits.
    :raise: ValueError if the value falls outside limits."""
    if 0 <= value <= 100:
        return True
    else:
        raise ValueError(str(value) + ' humidity value fails check')


def windspeed_check(value):
    """Check the windspeed value falls within reasonable limits.
        :param value: The windspeed value in knots.
        :return: True if the value falls with limits.
        :raise: ValueError if the value falls outside limits."""
    if 0 <= value < 500:
        return True
    else:
        raise ValueError(str(value) + ' windspeed value fails check')


def winddir_check(value):
    """Check the wind direction value falls within reasonable limits.
        :param value: The wind direction value in degrees.
        :return: True if the value falls with limits.
        :raise: ValueError if the value falls outside limits."""
    if 0 <= value <= 360:
        return True
    else:
        raise ValueError(str(value) + ' windspeed value fails check')
