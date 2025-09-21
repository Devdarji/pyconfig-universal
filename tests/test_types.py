"""Tests for type validation system."""

import pytest
from pyconfig.core.types import (
    StringValidator, IntValidator, FloatValidator, BoolValidator,
    ListValidator, DictValidator, UrlValidator, EmailValidator,
    PathValidator, DurationValidator, get_validator
)
from pyconfig.core.exceptions import ValidationError


class TestStringValidator:
    """Test string type validation."""
    
    def test_basic_string_validation(self):
        validator = StringValidator()
        assert validator.validate('key', 'test') == 'test'
        assert validator.validate('key', 123) == '123'
    
    def test_string_length_validation(self):
        validator = StringValidator(min_length=3, max_length=10)
        
        assert validator.validate('key', 'hello') == 'hello'
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'hi')  # Too short
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'this is too long')  # Too long
    
    def test_string_regex_validation(self):
        validator = StringValidator(regex=r'^[a-z]+$')
        
        assert validator.validate('key', 'hello') == 'hello'
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'Hello')  # Contains uppercase
    
    def test_string_strip(self):
        validator = StringValidator(strip=True)
        assert validator.validate('key', '  hello  ') == 'hello'


class TestIntValidator:
    """Test integer type validation."""
    
    def test_basic_int_validation(self):
        validator = IntValidator()
        assert validator.validate('key', 42) == 42
        assert validator.validate('key', '42') == 42
        assert validator.validate('key', '  42  ') == 42
    
    def test_int_range_validation(self):
        validator = IntValidator(range=[1, 100])
        
        assert validator.validate('key', 50) == 50
        
        with pytest.raises(ValidationError):
            validator.validate('key', 0)  # Below range
        
        with pytest.raises(ValidationError):
            validator.validate('key', 101)  # Above range
    
    def test_int_multiple_validation(self):
        validator = IntValidator(multiple_of=5)
        
        assert validator.validate('key', 10) == 10
        
        with pytest.raises(ValidationError):
            validator.validate('key', 7)  # Not multiple of 5
    
    def test_invalid_int(self):
        validator = IntValidator()
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'not_a_number')


class TestBoolValidator:
    """Test boolean type validation."""
    
    def test_basic_bool_validation(self):
        validator = BoolValidator()
        
        # True values
        assert validator.validate('key', True) is True
        assert validator.validate('key', 'true') is True
        assert validator.validate('key', 'TRUE') is True
        assert validator.validate('key', '1') is True
        assert validator.validate('key', 'yes') is True
        assert validator.validate('key', 'on') is True
        assert validator.validate('key', 1) is True
        
        # False values
        assert validator.validate('key', False) is False
        assert validator.validate('key', 'false') is False
        assert validator.validate('key', 'FALSE') is False
        assert validator.validate('key', '0') is False
        assert validator.validate('key', 'no') is False
        assert validator.validate('key', 'off') is False
        assert validator.validate('key', 0) is False
    
    def test_invalid_bool(self):
        validator = BoolValidator()
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'maybe')


class TestListValidator:
    """Test list type validation."""
    
    def test_basic_list_validation(self):
        validator = ListValidator()
        
        assert validator.validate('key', [1, 2, 3]) == [1, 2, 3]
        assert validator.validate('key', 'a,b,c') == ['a', 'b', 'c']
        assert validator.validate('key', 'single') == ['single']
    
    def test_list_length_validation(self):
        validator = ListValidator(min_items=2, max_items=4)
        
        assert validator.validate('key', [1, 2, 3]) == [1, 2, 3]
        
        with pytest.raises(ValidationError):
            validator.validate('key', [1])  # Too few items
        
        with pytest.raises(ValidationError):
            validator.validate('key', [1, 2, 3, 4, 5])  # Too many items
    
    def test_list_uniqueness(self):
        validator = ListValidator(unique=True)
        
        assert validator.validate('key', [1, 2, 3]) == [1, 2, 3]
        
        with pytest.raises(ValidationError):
            validator.validate('key', [1, 2, 2, 3])  # Duplicate items
    
    def test_list_item_validation(self):
        item_validator = IntValidator()
        validator = ListValidator(item_validator=item_validator)
        
        assert validator.validate('key', ['1', '2', '3']) == [1, 2, 3]
        
        with pytest.raises(ValidationError):
            validator.validate('key', ['1', 'not_int', '3'])


class TestUrlValidator:
    """Test URL type validation."""
    
    def test_basic_url_validation(self):
        validator = UrlValidator()
        
        assert validator.validate('key', 'https://example.com') == 'https://example.com'
        assert validator.validate('key', 'http://localhost:8000') == 'http://localhost:8000'
    
    def test_url_scheme_validation(self):
        validator = UrlValidator(schemes=['https'])
        
        assert validator.validate('key', 'https://example.com') == 'https://example.com'
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'http://example.com')  # Wrong scheme
    
    def test_url_no_localhost(self):
        validator = UrlValidator(no_localhost=True)
        
        assert validator.validate('key', 'https://example.com') == 'https://example.com'
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'https://localhost')
    
    def test_invalid_url(self):
        validator = UrlValidator()
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'not_a_url')
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'example.com')  # No scheme


class TestEmailValidator:
    """Test email type validation."""
    
    def test_basic_email_validation(self):
        validator = EmailValidator()
        
        assert validator.validate('key', 'user@example.com') == 'user@example.com'
        assert validator.validate('key', 'test.email+tag@domain.co.uk') == 'test.email+tag@domain.co.uk'
    
    def test_email_domain_validation(self):
        validator = EmailValidator(domains=['example.com', 'test.org'])
        
        assert validator.validate('key', 'user@example.com') == 'user@example.com'
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'user@other.com')  # Wrong domain
    
    def test_invalid_email(self):
        validator = EmailValidator()
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'not_an_email')
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'user@')


class TestDurationValidator:
    """Test duration type validation."""
    
    def test_basic_duration_validation(self):
        validator = DurationValidator()
        
        assert validator.validate('key', '30s') == 30
        assert validator.validate('key', '5m') == 300
        assert validator.validate('key', '2h') == 7200
        assert validator.validate('key', '1d') == 86400
        assert validator.validate('key', 60) == 60
    
    def test_duration_range_validation(self):
        validator = DurationValidator(min='10s', max='1h')
        
        assert validator.validate('key', '30s') == 30
        
        with pytest.raises(ValidationError):
            validator.validate('key', '5s')  # Below minimum
        
        with pytest.raises(ValidationError):
            validator.validate('key', '2h')  # Above maximum
    
    def test_invalid_duration(self):
        validator = DurationValidator()
        
        with pytest.raises(ValidationError):
            validator.validate('key', 'invalid')


class TestGetValidator:
    """Test validator factory function."""
    
    def test_get_string_validator(self):
        validator = get_validator('string', min_length=5)
        assert isinstance(validator, StringValidator)
        assert validator.options['min_length'] == 5
    
    def test_get_int_validator(self):
        validator = get_validator('int', range=[1, 100])
        assert isinstance(validator, IntValidator)
        assert validator.options['range'] == [1, 100]
    
    def test_unknown_type(self):
        with pytest.raises(ValueError):
            get_validator('unknown_type')
    
    def test_type_aliases(self):
        # Test that aliases work
        str_validator = get_validator('str')
        assert isinstance(str_validator, StringValidator)
        
        int_validator = get_validator('integer')
        assert isinstance(int_validator, IntValidator)
        
        bool_validator = get_validator('boolean')
        assert isinstance(bool_validator, BoolValidator)
