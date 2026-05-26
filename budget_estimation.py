import json
import re

def check_budget_constraints(plan, constraints, data):
    """
    Check if the plan satisfies the budget constraints.
    
    Args:
        plan: The generated travel plan (dictionary)
        constraints: Budget constraints from the query
        data: Database containing price information
    
    Returns:
        dict: Results of budget constraint checks
    """
    results = {}
    
    # Extract budget from constraints
    budget = constraints.get('budget', None)
    if budget is None:
        return {'budget_check': 'No budget constraint specified'}
    
    total_cost = 0
    cost_breakdown = {}
    
    # Calculate transportation costs
    if 'transportation' in plan:
        transport_cost = 0
        for leg in plan['transportation']:
            if 'cost' in leg:
                transport_cost += leg['cost']
            elif 'flight_number' in leg:
                # Look up flight cost from database
                flight_info = data.get('flights', {}).get(leg['flight_number'], {})
                transport_cost += flight_info.get('price', 0)
        total_cost += transport_cost
        cost_breakdown['transportation'] = transport_cost
    
    # Calculate accommodation costs
    if 'accommodation' in plan:
        accomm_cost = 0
        for stay in plan['accommodation']:
            if 'cost' in stay:
                accomm_cost += stay['cost'] * stay.get('nights', 1)
            elif 'hotel_name' in stay:
                hotel_info = data.get('hotels', {}).get(stay['hotel_name'], {})
                accomm_cost += hotel_info.get('price_per_night', 0) * stay.get('nights', 1)
        total_cost += accomm_cost
        cost_breakdown['accommodation'] = accomm_cost
    
    # Calculate attraction costs
    if 'attractions' in plan:
        attraction_cost = 0
        for attr in plan['attractions']:
            if 'cost' in attr:
                attraction_cost += attr['cost']
            elif 'attraction_name' in attr:
                attr_info = data.get('attractions', {}).get(attr['attraction_name'], {})
                attraction_cost += attr_info.get('ticket_price', 0)
        total_cost += attraction_cost
        cost_breakdown['attractions'] = attraction_cost
    
    # Calculate restaurant costs
    if 'restaurants' in plan:
        restaurant_cost = 0
        for meal in plan['restaurants']:
            if 'cost' in meal:
                restaurant_cost += meal['cost']
            elif 'restaurant_name' in meal:
                rest_info = data.get('restaurants', {}).get(meal['restaurant_name'], {})
                restaurant_cost += rest_info.get('average_price', 0)
        total_cost += restaurant_cost
        cost_breakdown['restaurants'] = restaurant_cost
    
    results['total_cost'] = total_cost
    results['budget_limit'] = budget
    results['within_budget'] = total_cost <= budget
    results['cost_breakdown'] = cost_breakdown
    results['remaining_budget'] = budget - total_cost
    
    return results


def estimate_budget_from_query(query):
    """
    Extract budget information from user query.
    
    Args:
        query: Natural language query string
    
    Returns:
        dict: Extracted budget information
    """
    budget_info = {
        'total_budget': None,
        'daily_budget': None,
        'currency': 'USD'
    }
    
    # Pattern for total budget
    total_patterns = [
        r'(?:total\s+)?budget\s+(?:is|of|:)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|USD)?',
        r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|USD)?\s+(?:total\s+)?budget',
        r'(?:have|got|with)\s+\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|USD)?',
    ]
    
    for pattern in total_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            budget_str = match.group(1).replace(',', '')
            budget_info['total_budget'] = float(budget_str)
            break
    
    # Pattern for daily budget
    daily_patterns = [
        r'(?:daily|per\s+day)\s+(?:budget\s+(?:is|of|:)?)?\s*\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|USD)?',
        r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|USD)?\s+(?:daily|per\s+day)',
    ]
    
    for pattern in daily_patterns:
        match = re.search(pattern, query, re.IGNORECASE)
        if match:
            budget_str = match.group(1).replace(',', '')
            budget_info['daily_budget'] = float(budget_str)
            break
    
    # Detect currency
    if re.search(r'€|euros?|EUR', query, re.IGNORECASE):
        budget_info['currency'] = 'EUR'
    elif re.search(r'£|pounds?|GBP', query, re.IGNORECASE):
        budget_info['currency'] = 'GBP'
    elif re.search(r'¥|yen|JPY', query, re.IGNORECASE):
        budget_info['currency'] = 'JPY'
    
    return budget_info


def estimate_trip_cost(destination, days, preferences=None):
    """
    Estimate the total cost of a trip based on destination and duration.
    
    Args:
        destination: City or country name
        days: Number of days for the trip
        preferences: Optional dictionary with travel preferences
    
    Returns:
        dict: Cost estimation breakdown
    """
    # Base costs per destination (simplified model)
    city_costs = {
        'new york': {'flight': 350, 'hotel': 200, 'food': 60, 'attractions': 40},
        'los angeles': {'flight': 300, 'hotel': 180, 'food': 55, 'attractions': 50},
        'chicago': {'flight': 250, 'hotel': 160, 'food': 50, 'attractions': 35},
        'san francisco': {'flight': 320, 'hotel': 220, 'food': 65, 'attractions': 45},
        'miami': {'flight': 280, 'hotel': 170, 'food': 55, 'attractions': 40},
        'las vegas': {'flight': 250, 'hotel': 150, 'food': 50, 'attractions': 60},
        'london': {'flight': 600, 'hotel': 250, 'food': 70, 'attractions': 50},
        'paris': {'flight': 650, 'hotel': 230, 'food': 65, 'attractions': 45},
        'tokyo': {'flight': 800, 'hotel': 180, 'food': 55, 'attractions': 40},
        'sydney': {'flight': 900, 'hotel': 200, 'food': 60, 'attractions': 45},
    }
    
    dest_lower = destination.lower()
    costs = city_costs.get(dest_lower, {'flight': 400, 'hotel': 180, 'food': 55, 'attractions': 40})
    
    estimation = {
        'destination': destination,
        'days': days,
        'flight_cost': costs['flight'],
        'hotel_cost': costs['hotel'] * days,
        'food_cost': costs['food'] * days,
        'attractions_cost': costs['attractions'] * days,
        'total_estimate': costs['flight'] + (costs['hotel'] + costs['food'] + costs['attractions']) * days
    }
    
    # Adjust for preferences
    if preferences:
        if preferences.get('luxury', False):
            for key in ['hotel_cost', 'food_cost', 'attractions_cost']:
                estimation[key] *= 1.5
        elif preferences.get('budget', False):
            for key in ['hotel_cost', 'food_cost', 'attractions_cost']:
                estimation[key] *= 0.6
        
        # Recalculate total
        estimation['total_estimate'] = (
            estimation['flight_cost'] + 
            estimation['hotel_cost'] + 
            estimation['food_cost'] + 
            estimation['attractions_cost']
        )
    
    return estimation


if __name__ == '__main__':
    # Example usage
    sample_query = "I want to plan a 5-day trip to New York with a total budget of $2000"
    
    budget_info = estimate_budget_from_query(sample_query)
    print(f"Extracted budget info: {json.dumps(budget_info, indent=2)}")
    
    trip_estimate = estimate_trip_cost('New York', 5)
    print(f"\nTrip cost estimate: {json.dumps(trip_estimate, indent=2)}")
    
    # Check if estimated cost is within budget
    if budget_info['total_budget']:
        is_affordable = trip_estimate['total_estimate'] <= budget_info['total_budget']
        print(f"\nIs trip within budget? {is_affordable}")
        print(f"Budget: ${budget_info['total_budget']:.2f}")
        print(f"Estimated: ${trip_estimate['total_estimate']:.2f}")
        print(f"Difference: ${budget_info['total_budget'] - trip_estimate['total_estimate']:.2f}")
