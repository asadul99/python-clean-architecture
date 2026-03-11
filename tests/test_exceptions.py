"""
Domain exceptions unit tests — test the custom exception hierarchy.

In C#:
    [Fact]
    public void NotFoundException_Has_Correct_Message() {
        var ex = new NotFoundException("Order", 42);
        Assert.Contains("Order", ex.Message);
        Assert.Contains("42", ex.Message);
    }
"""

import pytest
from domain.exceptions import (
    DomainException,
    NotFoundException,
    BusinessRuleViolationException,
    ConflictException,
)


class TestDomainExceptions:
    """Test the domain exception hierarchy."""

    def test_not_found_exception_message(self):
        ex = NotFoundException("Order", 42)
        assert "Order" in ex.message
        assert "42" in ex.message
        assert ex.entity_name == "Order"
        assert ex.entity_id == 42

    def test_not_found_exception_is_domain_exception(self):
        ex = NotFoundException("Order", 42)
        assert isinstance(ex, DomainException)

    def test_business_rule_violation_message(self):
        ex = BusinessRuleViolationException("Quantity must be positive")
        assert "Quantity must be positive" in ex.message
        assert ex.rule == "Quantity must be positive"

    def test_business_rule_violation_is_domain_exception(self):
        ex = BusinessRuleViolationException("test")
        assert isinstance(ex, DomainException)

    def test_conflict_exception_message(self):
        ex = ConflictException("Order already exists")
        assert "Order already exists" in ex.message

    def test_conflict_exception_is_domain_exception(self):
        ex = ConflictException("test")
        assert isinstance(ex, DomainException)

    def test_domain_exception_is_base_exception(self):
        ex = DomainException("generic error")
        assert isinstance(ex, Exception)
        assert ex.message == "generic error"

